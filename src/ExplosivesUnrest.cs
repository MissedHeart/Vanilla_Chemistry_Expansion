// Selling two or more bundles of dynamite in one day to Lower Levels or Revolution buyers always sets off a price
// rise the next day: one of vanilla's own normal events that raises prices (any of its negotiation values above
// zero: seed heist, bad Nutrifruit harvest, counterfeit medical supplies, lower level mob justice, power shortage,
// ...), drawn by vanilla's own odds. The list is read from StoreEventManager.normalEventBlueprints when it fires, so
// it follows the game. Sales are counted as they happen (SoldItem.TrackItem); on the second qualifying sale the event
// goes into the vanilla event queue for tomorrow, so it opens the next day with the news and calendar.
// Written for C# 5 (see DreamToxinMod.cs).
using System;
using System.Collections.Generic;
using HarmonyLib;

public static class ExplosivesUnrest
{
    public const int SALES_NEEDED = 2;
    private const string SALES_KEY = "dynamite_unrest_sales";  // "day,count"

    private static readonly string[] Factions = { "FACTION_LOWER_LEVEL", "FACTION_REVOLUTION" };

    public static void OnSold(GameItem item, StoreClient client)
    {
        if (item == null || client == null || item.identifier != Dynamite.ITEM_ID || Array.IndexOf(Factions, client.clientFaction) < 0)
        {
            return;
        }
        int today = StoreStation.Instance.dayCounter;
        int count = 0;
        string saved = ModHelper.GetModData(DreamToxinMod.MOD_ID, SALES_KEY, null);
        if (!string.IsNullOrEmpty(saved))
        {
            string[] parts = saved.Split(',');
            int day, sold;
            if (parts.Length == 2 && int.TryParse(parts[0], out day) && int.TryParse(parts[1], out sold) && day == today)
            {
                count = sold;
            }
        }
        count++;
        ModHelper.SetModData(DreamToxinMod.MOD_ID, SALES_KEY, today + "," + count);
        Log.Info("dynamite sold to " + client.clientFaction + ": " + count + " today");
        if (count == SALES_NEEDED)
        {
            StoreEvent picked = PickPriceRise();
            if (picked == null)
            {
                Log.Info("no vanilla price-rise event to queue");
                return;
            }
            StoreStation.Instance.storeEventManager.QueueFuturEvent(picked, 1, true);
            Log.Info("price-rise event " + picked.identifier + " queued for day " + (today + 1));
        }
    }

    // A fresh copy of one vanilla normal event with a price rise in it, weighted by its blueprint odds.
    public static StoreEvent PickPriceRise()
    {
        List<StoreEvent> candidates = new List<StoreEvent>();
        List<int> weights = new List<int>();
        int total = 0;
        foreach (StoreEventBlueprint blueprint in StoreEventManager.normalEventBlueprints)
        {
            StoreEvent storeEvent;
            try
            {
                storeEvent = blueprint.storeEventFunc != null ? blueprint.storeEventFunc() : null;
            }
            catch (Exception e)
            {
                Log.Error("building vanilla event " + blueprint.identifier + " failed", e);
                continue;
            }
            if (storeEvent == null || !RaisesPrices(storeEvent))
            {
                continue;
            }
            int weight = Math.Max(1, blueprint.odd);
            candidates.Add(storeEvent);
            weights.Add(weight);
            total += weight;
        }
        if (candidates.Count == 0)
        {
            return null;
        }
        int roll = new Random().Next(total);
        for (int i = 0; i < candidates.Count; i++)
        {
            roll -= weights[i];
            if (roll < 0)
            {
                return candidates[i];
            }
        }
        return candidates[candidates.Count - 1];
    }

    private static bool RaisesPrices(StoreEvent storeEvent)
    {
        if (storeEvent.negociationDatas == null)
        {
            return false;
        }
        foreach (NegociationData data in storeEvent.negociationDatas)
        {
            if (data != null && data.value > 0)
            {
                return true;
            }
        }
        return false;
    }
}

[HarmonyPatch(typeof(SoldItem), "TrackItem")]
public static class ExplosivesUnrestSalePatch
{
    private static void Postfix(GameItem gameItem, StoreClient storeClient)
    {
        try
        {
            ExplosivesUnrest.OnSold(gameItem, storeClient);
        }
        catch (Exception e)
        {
            Log.Error("counting dynamite sales failed", e);
        }
    }
}
