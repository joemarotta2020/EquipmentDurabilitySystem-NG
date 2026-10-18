#include "ArmorClassifier.h"

namespace
{
    std::uint32_t GetArmorSlotMask(RE::TESObjectARMO* armor)
    {
        if (!armor)
            return 0;

        std::uint32_t slots = 0;
        for (int slot = 30; slot <= 61; ++slot) {
            const auto flag = static_cast<RE::BGSBipedObjectForm::BipedObjectSlot>(EDArmor::SlotBit(slot));
            if (armor->HasPartOf(flag))
                slots |= EDArmor::SlotBit(slot);
        }
        return slots;
    }

    EDArmor::SemanticFlags GetSemanticFlags(RE::TESObjectARMO* armor)
    {
        EDArmor::SemanticFlags result{};
        if (!armor)
            return result;

        auto* dataHandler = RE::TESDataHandler::GetSingleton();
        if (!dataHandler)
            return result;

        static auto* armorCuirass = dataHandler->LookupForm<RE::BGSKeyword>(0x6C0EC, "Skyrim.esm");
        static auto* armorBoots = dataHandler->LookupForm<RE::BGSKeyword>(0x6C0ED, "Skyrim.esm");
        static auto* armorHelmet = dataHandler->LookupForm<RE::BGSKeyword>(0x6C0EE, "Skyrim.esm");
        static auto* armorGauntlets = dataHandler->LookupForm<RE::BGSKeyword>(0x6C0EF, "Skyrim.esm");

        result.helmet = armorHelmet && armor->HasKeyword(armorHelmet);
        result.cuirass = armorCuirass && armor->HasKeyword(armorCuirass);
        result.gauntlets = armorGauntlets && armor->HasKeyword(armorGauntlets);
        result.boots = armorBoots && armor->HasKeyword(armorBoots);
        return result;
    }

    std::string_view GetOriginPluginName(RE::TESObjectARMO* armor)
    {
        if (!armor)
            return {};

        auto* file = armor->GetFile(0);
        return file ? std::string_view(file->fileName) : std::string_view{};
    }
}

EDArmor::Region EDArmor::ClassifyArmor(RE::TESObjectARMO* armor)
{
    if (!armor)
        return Region::Unknown;

    return Classify(GetOriginPluginName(armor), GetArmorSlotMask(armor), GetSemanticFlags(armor));
}
