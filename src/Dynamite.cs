// Dynamite: a bundle of sticks pressed in the Chem Finisher from dry TNT (FlavorChemistry.TNT). Like the vanilla
// breaching C4 it is a weapon and munition at contraband level 3 (+100% markup).
//
// Balance (per 80 g coffee bean, same purity grade either way):
//   caffeine pills: 4.4 mL caffeine + 75% of 25.8 mL mush by alcohol extraction = 23.75 mL; a pill is 5 mL for 10,
//                   so 47.5 a bean.
//   dynamite:       the same caffeine turned to fat at 150 C plus the bean's 8 mL of fat = 31.75 mL fat -> 25.4 mL
//                   toluene -> 25.4 mL TNT (with 76.2 mL nitric acid, i.e. 76.2 mL nitric oxide from the
//                   electrolyzer). 1.26 a mL (315 per 250 mL) x2 contraband markup = 64.0, less about 0.8 of battery
//                   power (0.2 nights of nitric oxide at 375 mL a night + 0.13 of fat electrolysis, at 24 power a night
//                   and 0.1 a unit) = 63.2, about 33% over pills.
// One bundle is 250 mL of TNT: about 10 beans' worth, and 750 mL of nitric oxide, two electrolyzer nights.
// Written for C# 5 (see DreamToxinMod.cs).
using System;

public static class Dynamite
{
    public const string ITEM_ID = "vce_dynamite";
    public const string SPRITE = "vce_dynamite";
    public const int REQUIRED_VOLUME = 250000;
    public const long VALUE = 315;
    public const int CONTRABAND_LEVEL = 3;

    public static void Register()
    {
        if (FinisherRecipes.Find(ITEM_ID) != null)
        {
            return;
        }
        ChemFinisherRecipe recipe = new ChemFinisherRecipe();
        recipe.identifier = ITEM_ID;
        recipe.displayName = IaText.Get("dynamite_name");
        recipe.requiredVolume = REQUIRED_VOLUME;
        recipe.isRequireDry = true;
        recipe.activeIngredientId = FlavorChemistry.TNT;
        ChemFinisherRecipe.chemFinisherRecipes.Add(recipe);
    }

    public static void Unregister()
    {
        ChemFinisherRecipe.chemFinisherRecipes.RemoveAll(r => r.identifier == ITEM_ID);
    }

    public static void RefreshNames()
    {
        ChemFinisherRecipe recipe = FinisherRecipes.Find(ITEM_ID);
        if (recipe != null)
        {
            recipe.displayName = IaText.Get("dynamite_name");
        }
    }

    public static void AddItems(ModItemDirectory directory)
    {
        directory.Add(ITEM_ID, Create);
    }

    public static GameItem Create()
    {
        GameItem item = ItemDirectory.CreateEmptyItem(ITEM_ID);
        try
        {
            item.name = IaText.Get("dynamite_name");
            item.shortDescription = IaText.Get("dynamite_desc");
            item.flavorText = IaText.Get("dynamite_flavor");
            item.unitValue = VALUE;
            item.SetGameItemType("WEAPON");
            item.SetGameItemType("MUNITION");
            ContrabandHelper.InitContrabandItem(item, CONTRABAND_LEVEL);
            ChemicalHelper.InitChemItem(item, false, false);
            // Default contents for bundles not made in the Chem Finisher (debug spawns): street grade.
            ChemFinisherRecipe.SetCompositionByPurity(item, 60, 80, REQUIRED_VOLUME, FlavorChemistry.TNT);
            ChemicalProductHelper.InitChemicalProduct(item, FlavorChemistry.TNT);
            AudioHelper.InitSolidMetal(item);
            BeerSprites.Apply(item, SPRITE);
            ModHelper.SetSource(item, DreamToxinMod.MOD_ID, DreamToxinMod.MOD_NAME);
        }
        catch (Exception e)
        {
            IaLog.Error("create " + ITEM_ID + " failed", e);
        }
        return item;
    }

    public static void SpawnKit()
    {
        try
        {
            GameItem item = DirectoryMaster.Item(ITEM_ID, true);
            ChemicalProductHelper.GradeProduct(item);
            GraphUtils.TryAcceptAll(EmporiumEntry.Instance.invElement, item);
        }
        catch (Exception e)
        {
            IaLog.Error("dynamite debug kit failed", e);
        }
    }
}
