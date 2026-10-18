#pragma once

#include <cstdint>
#include <string_view>

namespace EDArmor
{
    enum class Region : std::uint8_t
    {
        Unknown,
        Head,
        Hands,
        Feet,
        BodyTorso,
        BodyPelvisLegs,
        BodyShouldersBack
    };

    struct SemanticFlags
    {
        bool helmet{ false };
        bool cuirass{ false };
        bool gauntlets{ false };
        bool boots{ false };
    };

    constexpr std::uint32_t SlotBit(int slot)
    {
        return slot >= 30 && slot <= 61
            ? (std::uint32_t{ 1 } << static_cast<unsigned>(slot - 30))
            : 0u;
    }

    constexpr bool HasSlot(std::uint32_t slots, int slot)
    {
        return (slots & SlotBit(slot)) != 0;
    }

    constexpr char LowerAscii(char value)
    {
        return value >= 'A' && value <= 'Z'
            ? static_cast<char>(value + ('a' - 'A'))
            : value;
    }

    constexpr bool EqualsIgnoreCase(std::string_view left, std::string_view right)
    {
        if (left.size() != right.size())
            return false;

        for (std::size_t i = 0; i < left.size(); ++i) {
            if (LowerAscii(left[i]) != LowerAscii(right[i]))
                return false;
        }

        return true;
    }

    constexpr bool IsKnownModularPlugin(std::string_view pluginName)
    {
        return EqualsIgnoreCase(pluginName, "The Amazing World of Bikini Armors REMASTERED.esp") ||
            EqualsIgnoreCase(pluginName, "(Pumpkin)-TEWOBA-TheExpandedWorldofBikiniArmor.esp");
    }

    constexpr Region ClassifyKnownModular(std::uint32_t slots)
    {
        // Head equipment and face/neck pieces used by TAWOBA/TEWOBA.
        if (HasSlot(slots, 30) || HasSlot(slots, 31) || HasSlot(slots, 41) ||
            HasSlot(slots, 42) || HasSlot(slots, 43) || HasSlot(slots, 44) ||
            HasSlot(slots, 45))
            return Region::Head;

        // Slot 32 is authoritative for integrated torso pieces. This also keeps
        // one-piece/cyborg records from being misclassified by their extra limbs.
        if (HasSlot(slots, 32))
            return Region::BodyTorso;

        // Shoulder/back pieces can also occupy auxiliary chest/targe slots.
        if (HasSlot(slots, 47) || HasSlot(slots, 57) || HasSlot(slots, 58))
            return Region::BodyShouldersBack;

        if (HasSlot(slots, 33) || HasSlot(slots, 34))
            return Region::Hands;

        if (HasSlot(slots, 37) || HasSlot(slots, 38))
            return Region::Feet;

        if (HasSlot(slots, 46) || HasSlot(slots, 48) || HasSlot(slots, 56))
            return Region::BodyTorso;

        if (HasSlot(slots, 49) || HasSlot(slots, 52) || HasSlot(slots, 53) || HasSlot(slots, 54))
            return Region::BodyPelvisLegs;

        // Slot 60 is intentionally not assigned: the supplied TAWOBA plugin uses
        // it for unrelated masks, crowns and gauntlet pieces.
        return Region::Unknown;
    }

    constexpr Region Classify(std::string_view pluginName, std::uint32_t slots, SemanticFlags semantics)
    {
        // Known modular armor uses its plugin-scoped slot convention first.
        // The supplied plugins reuse vanilla ArmorCuirass/Helmet/etc. keywords
        // on many modular pieces, so semantic keywords are not authoritative here.
        if (IsKnownModularPlugin(pluginName)) {
            const auto modular = ClassifyKnownModular(slots);
            if (modular != Region::Unknown)
                return modular;
        }

        // For ordinary armor, semantic identity survives slot-moving patchers
        // such as SynInvisibleHelmets and therefore takes priority over slots.
        if (semantics.helmet)
            return Region::Head;
        if (semantics.cuirass)
            return Region::BodyTorso;
        if (semantics.gauntlets)
            return Region::Hands;
        if (semantics.boots)
            return Region::Feet;

        // Conservative vanilla slot fallback. Auxiliary 44+ slots are deliberately
        // not given global meaning outside configured modular plugins.
        if (HasSlot(slots, 30) || HasSlot(slots, 31) || HasSlot(slots, 41) ||
            HasSlot(slots, 42) || HasSlot(slots, 43))
            return Region::Head;
        if (HasSlot(slots, 32) || HasSlot(slots, 40))
            return Region::BodyTorso;
        if (HasSlot(slots, 33) || HasSlot(slots, 34))
            return Region::Hands;
        if (HasSlot(slots, 37) || HasSlot(slots, 38))
            return Region::Feet;

        return Region::Unknown;
    }
}
