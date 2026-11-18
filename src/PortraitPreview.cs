// Portrait preview: puts the chemist father and son portraits (Textures/Items/vce_portrait_*.png, 288x211 like
// vanilla client portraits) on three ordinary customers, to see how they look in the shop. A save carrying the mod
// data flag "vanilla_chem_ext:portrait_preview" = "1" gets them once, at the front of the queue: straight away when
// the day's customers already exist on load, otherwise when the next day's customers are generated. The flag is then
// set to "given". Written for C# 5 (see DreamToxinMod.cs).
using System;
using HarmonyLib;
using UnityEngine;

public static class PortraitPreview
{
    public const string FLAG_KEY = "portrait_preview";
    public const string SPRITE_PREFIX = "vce_portrait_";

    private static readonly string[] Portraits = { "vce_portrait_father", "vce_portrait_son_jacket", "vce_portrait_son_coat" };

    public static void Enable()
    {
        ModHook.OnGameLoadedLate += OnGameLoaded;
        ModHook.OnGenerateCustomerNormal += OnGenerateCustomers;
    }

    public static void Disable()
    {
        ModHook.OnGameLoadedLate -= OnGameLoaded;
        ModHook.OnGenerateCustomerNormal -= OnGenerateCustomers;
    }

    private static bool Pending()
    {
        return ModHelper.GetModData(DreamToxinMod.MOD_ID, FLAG_KEY, null) == AntibioticTestKit.FLAG_PENDING;
    }

    private static void OnGameLoaded()
    {
        try
        {
            StoreClientManager manager = PlayerStore.Instance == null ? null : PlayerStore.Instance.storeClientManager;
            if (Pending() && manager != null && manager.clientStack.Count > 0)
            {
                AddPreviewClients(manager);
            }
        }
        catch (Exception e)
        {
            Log.Error("portrait preview on load failed", e);
        }
    }

    private static void OnGenerateCustomers(StoreClientManager manager)
    {
        try
        {
            if (Pending() && manager != null)
            {
                AddPreviewClients(manager);
            }
        }
        catch (Exception e)
        {
            Log.Error("portrait preview customers failed", e);
        }
    }

    // Three ordinary food shoppers, first in line, each wearing one of the portraits.
    private static void AddPreviewClients(StoreClientManager manager)
    {
        ModHelper.SetModData(DreamToxinMod.MOD_ID, FLAG_KEY, AntibioticTestKit.FLAG_GIVEN);
        for (int i = Portraits.Length - 1; i >= 0; i--)
        {
            StoreClient client = StoreClientList.CreateSpacerClientFoodVariety();
            client.identifier = "vce_portrait_preview_" + i;
            client.spriteName = Portraits[i];
            ModHelper.SetClientSource(client, DreamToxinMod.MOD_ID);
            manager.clientStack.Insert(0, client);
        }
        Log.Info("portrait preview: three customers added to the front of the queue");
    }

    public static Sprite Find(string key)
    {
        CustomUIManager ui = CustomUIManager.Instance;
        return ui == null ? null : ui.GetModSprite(DreamToxinMod.MOD_ID, key, true);
    }
}

// Client portraits are looked up by key in vanilla's sprite dictionary; ours live in the mod's item sprites.
[HarmonyPatch(typeof(SpriteDict), "GetSprite", new Type[] { typeof(string) })]
public static class PortraitPreviewSpritePatch
{
    private static bool Prefix(string key, ref Sprite __result)
    {
        if (key == null || !key.StartsWith(PortraitPreview.SPRITE_PREFIX, StringComparison.Ordinal))
        {
            return true;
        }
        Sprite sprite = PortraitPreview.Find(key);
        if (sprite == null)
        {
            return true;
        }
        __result = sprite;
        return false;
    }
}
