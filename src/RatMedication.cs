// Medicated feed: an antibiotic tablet can go into a livestock feed dispenser and be blended like food (by the
// button or auto-blend). It adds no kcal; it marks the dispenser as medicated for the coming night. During that
// night's animal pass (vanilla runs every item's onCycleEndSlotItemFunc, HusbandryHelper.OnAnimalItemDayEnd for
// animals), every diseased animal in a cage that reaches the dispenser (the cage's dispenser slot, or a dispenser
// standing inside the cage, as vanilla's feeding does) loses its disease before the disease does its damage. The mark
// clears in the late pass of the same night (onCycleEndLateSlotItemFunc), so one tablet treats one night. One tablet
// per night per dispenser: while it is medicated, further tablets stay in its storage. Written for C# 5 (see
// DreamToxinMod.cs).
using System;
using HarmonyLib;

public static class RatMedication
{
    public const string MEDICATED_TAG = "VCE_DISPENSER_MEDICATED_TAG";
    public const string DISEASED_TAG = "ANIMAL_DISEASED_TAG";

    // A save carrying the mod data flag "vanilla_chem_ext:rat_medication_kit" = "1" gets the test kit once when it
    // loads (like AntibioticTestKit); the flag is set to "given" first.
    public const string KIT_FLAG_KEY = "rat_medication_kit";

    public static void Enable()
    {
        ModHook.OnCreateTooltipLate += OnCreateTooltip;
        ModHook.OnGameLoadedLate += OnGameLoaded;
        try
        {
            ModHelper.AddDebugFunction(DreamToxinMod.MOD_ID, "Modding", "Antibiotics: rat medication test kit", SpawnTestKit, false);
            ModHelper.AddDebugFunction(DreamToxinMod.MOD_ID, "Modding", "Antibiotics: make held rats diseased", MakeRatsDiseased, false);
        }
        catch (Exception e)
        {
            Log.Error("rat medication debug registration failed", e);
        }
    }

    private static void OnGameLoaded()
    {
        try
        {
            if (ModHelper.GetModData(DreamToxinMod.MOD_ID, KIT_FLAG_KEY, null) != AntibioticTestKit.FLAG_PENDING)
            {
                return;
            }
            ModHelper.SetModData(DreamToxinMod.MOD_ID, KIT_FLAG_KEY, AntibioticTestKit.FLAG_GIVEN);
            Log.Info("this save asked for the rat medication test kit");
            SpawnTestKit();
        }
        catch (Exception e)
        {
            Log.Error("giving the rat medication test kit on load failed", e);
        }
    }

    // Ready to run: a cage with a feed dispenser in its slot, already holding three large nutrifruits' worth of kcal,
    // four sick adult rats inside the cage, and five pharma-grade tablets next to it.
    public static void SpawnTestKit()
    {
        try
        {
            GameItem cage = DirectoryMaster.Item("animal_cage", true);
            GameItem dispenser = DirectoryMaster.Item("livestock_feed_dispenser", true);
            GameSlotInventory slot = AnimalCage.GetDispenserSlot(cage);
            if (slot != null && GraphUtils.TryAcceptAll(slot, dispenser) > 0)
            {
                Log.Info("rat medication test kit: the dispenser did not go into the cage slot");
                Place(dispenser, "feed dispenser");
            }
            for (int i = 0; i < 3; i++)
            {
                GameItem fruit = PreBuiltItemHelper.CreateNutrifruitLarge();
                if (!MachineFeedDispenser.TryBlendItem(dispenser, fruit))
                {
                    Place(fruit, "nutrifruit");
                }
            }
            GameGridInventory grid = AnimalCage.GetCageInventory(cage);
            foreach (string sex in new string[] { "MALE", "FEMALE", "MALE", "FEMALE" })
            {
                GameItem rat = PreBuiltItemHelper.CreateRat(sex, 5, true);
                rat.EnableTag(DISEASED_TAG, false);
                rat.EnableTag("IS_OWNED_TAG", false);
                if (grid == null || GraphUtils.TryAcceptAll(grid, rat) > 0)
                {
                    Place(rat, "rat");
                }
            }
            Place(cage, "animal cage");
            string genome = StrainTraits.RandomGenome();
            for (int i = 0; i < 5; i++)
            {
                GameItem tablet = DirectoryMaster.Item(Antibiotics.TABLET_ID, true);
                if (tablet == null)
                {
                    continue;
                }
                CephData.SetGenome(tablet, genome);
                CephData.SetInt(tablet, CephData.TARGET_LIQUID_TAG, Antibiotics.TABLET_VOLUME);
                ChemicalProductHelper.GradeProduct(tablet);
                Place(tablet, "antibiotic tablet");
            }
            Log.Info("rat medication test kit spawned");
        }
        catch (Exception e)
        {
            Log.Error("rat medication test kit failed", e);
        }
    }

    // Anywhere in the shop that takes it; EmporiumTryAdd destroys what fits nowhere, so say so.
    private static void Place(GameItem item, string what)
    {
        if (item == null)
        {
            return;
        }
        GraphUtils.EmporiumTryAdd(item);
        if (item.parentInventory == null)
        {
            Log.Info("rat medication test kit: no room for " + what);
        }
    }

    public static void MakeRatsDiseased()
    {
        try
        {
            int count = 0;
            foreach (GameItem item in EmporiumEntry.Instance.GetAllItems())
            {
                if (item != null && item.IsTag("ANIMAL_ITEM_TAG") && !item.IsTag("ANIMAL_IS_DEAD_TAG") && !item.IsTag(DISEASED_TAG))
                {
                    item.EnableTag(DISEASED_TAG, false);
                    count++;
                }
            }
            Log.Info("made " + count + " animal(s) diseased");
        }
        catch (Exception e)
        {
            Log.Error("making animals diseased failed", e);
        }
    }

    public static void Disable()
    {
        ModHook.OnCreateTooltipLate -= OnCreateTooltip;
        ModHook.OnGameLoadedLate -= OnGameLoaded;
    }

    public static bool IsMedicated(GameItem dispenser)
    {
        return dispenser != null && dispenser.IsTag(MEDICATED_TAG);
    }

    // The dispensers vanilla lets an animal in this inventory eat from.
    public static bool CageIsMedicated(GameInventory cage)
    {
        if (cage == null)
        {
            return false;
        }
        if (IsMedicated(AnimalCage.GetSlottedDispenser(cage)))
        {
            return true;
        }
        foreach (GameItem child in cage.childItems)
        {
            if (child != null && child.IsTag("FEED_DISPENSER_TAG") && IsMedicated(child))
            {
                return true;
            }
        }
        return false;
    }

    // Called from the dispenser's blend. True when the tablet was used.
    public static bool TryMedicate(GameItem dispenser, GameItem tablet)
    {
        if (dispenser == null || tablet == null || IsMedicated(dispenser))
        {
            return false;
        }
        dispenser.EnableTag(MEDICATED_TAG, false);
        if (tablet.unitCount > 1)
        {
            tablet.SetUnitCount(tablet.unitCount - 1);
        }
        else
        {
            tablet.Destroy();
        }
        Log.Info("feed dispenser medicated with an antibiotic tablet for tonight");
        return true;
    }

    public static void EndNight(GameItem dispenser)
    {
        if (IsMedicated(dispenser))
        {
            dispenser.DisableTag(MEDICATED_TAG, false);
        }
    }

    public static void OnCreateTooltip(RichTextBuilder builder, GameItem item)
    {
        try
        {
            if (builder != null && IsMedicated(item))
            {
                builder.AddLine(Text.Get("rat_medication_tooltip"), true, RenderHandler.ColorPalette.LightCyan);
            }
        }
        catch (Exception e)
        {
            Log.Error("medicated dispenser tooltip failed", e);
        }
    }
}

// Every feed dispenser (the stand-alone one, the one in a cage's slot, the one bolted into the fermenter) comes from
// this factory, saved ones included: let tablets into its storage and clear the mark after each night.
[HarmonyPatch(typeof(MachineFeedDispenser), "CreateFeedDispenser")]
public static class RatMedicationDispenserPatch
{
    private static void Postfix(GameItem __result)
    {
        try
        {
            GameItem machine = __result;
            if (machine == null)
            {
                return;
            }
            GameGridInventory storage = MachineFeedDispenser.GetStorageGrid(machine);
            if (storage != null)
            {
                Func<GameItem, GameInventory, bool> vanilla = storage.mayInventoryAddItemFunc;
                storage.mayInventoryAddItemFunc = delegate(GameItem item, GameInventory inv)
                {
                    if (vanilla != null && vanilla(item, inv))
                    {
                        return true;
                    }
                    return Antibiotics.IsTablet(item) && GeneralHelper.IsItemOwned(machine, item);
                };
            }
            machine.onCycleEndLateSlotItemFunc = (Action<GameItem, GameInventory, SlotMarker>)Delegate.Combine(
                machine.onCycleEndLateSlotItemFunc,
                (Action<GameItem, GameInventory, SlotMarker>)delegate(GameItem self, GameInventory inv, SlotMarker slot)
                {
                    RatMedication.EndNight(self);
                });
        }
        catch (Exception e)
        {
            Log.Error("preparing a feed dispenser for medicated feed failed", e);
        }
    }
}

// Blending: a tablet becomes tonight's medication instead of kcal.
[HarmonyPatch(typeof(MachineFeedDispenser), "TryBlendItem")]
public static class RatMedicationBlendPatch
{
    private static bool Prefix(GameItem machine, GameItem foodItem, ref bool __result)
    {
        if (!Antibiotics.IsTablet(foodItem))
        {
            return true;
        }
        try
        {
            __result = RatMedication.TryMedicate(machine, foodItem);
        }
        catch (Exception e)
        {
            Log.Error("medicating a feed dispenser failed", e);
            __result = false;
        }
        return false;
    }
}

// The night's disease step: a medicated cage cures the animal before the disease hurts it.
[HarmonyPatch(typeof(HusbandryHelper), "HandleDisease")]
public static class RatMedicationCurePatch
{
    private static void Prefix(GameItem item)
    {
        try
        {
            if (item == null || !item.IsTag(RatMedication.DISEASED_TAG))
            {
                return;
            }
            if (RatMedication.CageIsMedicated(item.parentInventory as GameInventory))
            {
                item.DisableTag(RatMedication.DISEASED_TAG, false);
                Log.Info("medicated feed cured a diseased animal");
            }
        }
        catch (Exception e)
        {
            Log.Error("medicated feed cure failed", e);
        }
    }
}
