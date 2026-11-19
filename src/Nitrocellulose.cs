// Nitrocellulose: drag a liquid container holding nitric acid (FlavorChemistry.NITRIC_ACID) onto an owned Kotton
// fiber; the nitric acid is used up and the fiber turns into nitrocellulose of the same size, in the same place.
//   small fiber (36)  -> 30 mL nitric acid -> small nitrocellulose (54)
//   fiber (46)        -> 40 mL             -> nitrocellulose (69)
//   large fiber (60)  -> 50 mL             -> large nitrocellulose (90)
// Each size is its own item (vce_nitrocellulose_s / vce_nitrocellulose / vce_nitrocellulose_l): a white clump of
// fibre without the stems, 1x1, 2x1 and 2x2 cells (art/explosives/draw_nitrocellulose.py). No further use yet.
// Written for C# 5 (see DreamToxinMod.cs).
using System;
using System.Collections.Generic;
using HarmonyLib;

public static class Nitrocellulose
{
    public const string FIBER_ID = "kotton_fiber";

    private class Size
    {
        public string ItemId;
        public string NameKey;
        public string VanillaSprite;
        public int NitricUl;
        public long Value;

        public Size(string itemId, string nameKey, string vanillaSprite, int nitricUl, long value)
        {
            ItemId = itemId;
            NameKey = nameKey;
            VanillaSprite = vanillaSprite;
            NitricUl = nitricUl;
            Value = value;
        }
    }

    private static readonly Size Small = new Size("vce_nitrocellulose_s", "nitrocellulose_s_name", "kotton_plant_s", 30000, 54);
    private static readonly Size Normal = new Size("vce_nitrocellulose", "nitrocellulose_name", "kotton_plant", 40000, 69);
    private static readonly Size Large = new Size("vce_nitrocellulose_l", "nitrocellulose_l_name", "kotton_plant_l", 50000, 90);
    private static readonly Size[] Sizes = { Small, Normal, Large };

    // Propellant the reloading press gets out of it: its value (ReloadingPress.cs).
    public static int PowderOf(GameItem item)
    {
        if (item == null)
        {
            return 0;
        }
        foreach (Size size in Sizes)
        {
            if (item.identifier == size.ItemId)
            {
                return (int)size.Value;
            }
        }
        return 0;
    }

    public static bool IsNitrocellulose(GameItem item)
    {
        if (item == null)
        {
            return false;
        }
        foreach (Size size in Sizes)
        {
            if (item.identifier == size.ItemId)
            {
                return true;
            }
        }
        return false;
    }

    public static void AddItems(ModItemDirectory directory)
    {
        foreach (Size size in Sizes)
        {
            Size s = size;
            directory.Add(s.ItemId, () => Create(s));
        }
    }

    private static GameItem Create(Size size)
    {
        GameItem item = ItemDirectory.CreateEmptyItem(size.ItemId);
        try
        {
            item.name = Text.Get(size.NameKey);
            item.shortDescription = Text.Get("nitrocellulose_desc");
            item.unitValue = size.Value;
            item.SetGameItemType("MATERIAL");
            AudioHelper.InitLeafy(item);
            BeerSprites.Apply(item, size.ItemId);
            ModHelper.SetSource(item, DreamToxinMod.MOD_ID, DreamToxinMod.MOD_NAME);
        }
        catch (Exception e)
        {
            Log.Error("create " + size.ItemId + " failed", e);
        }
        return item;
    }

    // The vanilla fiber comes in three sizes that differ only in sprite, name and value (PreBuiltItemHelper).
    private static Size SizeOf(GameItem fiber)
    {
        string sprite = fiber.spritePath ?? "";
        foreach (Size size in Sizes)
        {
            if (sprite == size.VanillaSprite)
            {
                return size;
            }
        }
        return fiber.unitValue <= 40 ? Small : fiber.unitValue >= 55 ? Large : Normal;
    }

    public static bool CanNitrate(GameItem source, GameItem target)
    {
        if (source == null || target == null || target.identifier != FIBER_ID || source == target)
        {
            return false;
        }
        if (!source.IsTag("LIQUID_CONTAINER_TAG") || !GeneralHelper.IsItemOwned(source) || !GeneralHelper.IsItemOwned(target))
        {
            return false;
        }
        return IaLiquids.Get(source, FlavorChemistry.NITRIC_ACID) >= SizeOf(target).NitricUl;
    }

    public static void Nitrate(GameItem container, GameItem fiber)
    {
        try
        {
            if (!CanNitrate(container, fiber))
            {
                return;
            }
            Size size = SizeOf(fiber);
            GameItem product = DirectoryMaster.Item(size.ItemId, true);
            if (product == null)
            {
                return;
            }
            ModHelper.SetItemOwnerShip(product, true);
            // The product takes the fiber's place; if it fits nowhere the fiber goes back and nothing is used up.
            GameInventory home = fiber.parentInventory;
            if (home != null)
            {
                home.Expel(fiber);
            }
            if (!Place(product, home))
            {
                if (home != null)
                {
                    GraphUtils.TryAcceptAll(home, fiber);
                }
                product.Destroy();
                return;
            }
            fiber.Destroy();
            IaLiquids.Set(container, FlavorChemistry.NITRIC_ACID, IaLiquids.Get(container, FlavorChemistry.NITRIC_ACID) - size.NitricUl);
            WaterFeatureHelper.OnLiquidContainerPourOutOf(container);
            SpriteHelper.UpdateWaterContainerSprite(container);
            AudioHelper.PourWater();
        }
        catch (Exception e)
        {
            Log.Error("nitrating Kotton fiber failed", e);
        }
    }

    private static bool Place(GameItem product, GameInventory home)
    {
        EmporiumEntry shop = EmporiumEntry.Instance;
        List<GameInventory> targets = new List<GameInventory>();
        if (home != null)
        {
            targets.Add(home);
        }
        if (shop != null)
        {
            targets.Add(shop.invElement);
            targets.Add(shop.showcaseElement);
            targets.Add(shop.frontInvinvElement);
            targets.Add(shop.backInvinvElement);
        }
        foreach (GameInventory target in targets)
        {
            if (ItemPlacement.TryPut(target, product))
            {
                return true;
            }
        }
        return false;
    }
}

// The fiber does the nitrating when a container is dropped on it.
[HarmonyPatch(typeof(HydroponicDirectory), "KottonPlant")]
public static class NitrocelluloseFiberPatch
{
    private static void Postfix(GameItem __result)
    {
        try
        {
            if (__result == null)
            {
                return;
            }
            __result.mayItemTargetThisFunc = (Func<GameItem, GameItem, bool>)Delegate.Combine(__result.mayItemTargetThisFunc,
                (Func<GameItem, GameItem, bool>)((GameItem s, GameItem t) => Nitrocellulose.CanNitrate(s, t)));
            __result.canItemTargetThisFunc = (Func<GameItem, GameItem, bool>)Delegate.Combine(__result.canItemTargetThisFunc,
                (Func<GameItem, GameItem, bool>)((GameItem s, GameItem t) => Nitrocellulose.CanNitrate(s, t)));
            __result.onItemTargetThisFunc = (Action<GameItem, GameItem>)Delegate.Combine(__result.onItemTargetThisFunc,
                (Action<GameItem, GameItem>)delegate(GameItem s, GameItem t) { Nitrocellulose.Nitrate(s, t); });
        }
        catch (Exception e)
        {
            Log.Error("Kotton fiber nitrating hook failed", e);
        }
    }
}

// A liquid container's own targeting rule refuses everything but containers, drains and faucets; this adds a yes for
// nitric acid onto Kotton fiber (see MutagenContainerPatch in StrainMutation.cs). The container's own action does
// nothing to a fiber.
[HarmonyPatch(typeof(WaterHelper), "InitLiquidContainerItem")]
public static class NitrocelluloseContainerPatch
{
    private static void Postfix(GameItem item)
    {
        try
        {
            if (item == null)
            {
                return;
            }
            item.mayThisTargetItemFunc = (Func<GameItem, GameItem, bool>)Delegate.Combine(item.mayThisTargetItemFunc,
                (Func<GameItem, GameItem, bool>)((GameItem s, GameItem t) => Nitrocellulose.CanNitrate(s, t)));
            item.canThisTargetItemFunc = (Func<GameItem, GameItem, bool>)Delegate.Combine(item.canThisTargetItemFunc,
                (Func<GameItem, GameItem, bool>)((GameItem s, GameItem t) => Nitrocellulose.CanNitrate(s, t)));
        }
        catch (Exception e)
        {
            Log.Error("letting liquid containers nitrate Kotton failed", e);
        }
    }
}
