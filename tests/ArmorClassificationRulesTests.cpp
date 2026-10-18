#include "../src/ArmorClassificationRules.h"

#include <cassert>
#include <cstdint>

using EDArmor::Region;
using EDArmor::SemanticFlags;

static constexpr std::uint32_t Slots(std::initializer_list<int> slots)
{
    std::uint32_t mask = 0;
    for (const int slot : slots)
        mask |= EDArmor::SlotBit(slot);
    return mask;
}

int main()
{
    // Invisible-helmet compatibility: semantic identity wins for ordinary armor
    // even when a Synthesis patcher has moved it to slot 61.
    assert(EDArmor::Classify("SynInvisHelmets.esp", Slots({61}), SemanticFlags{ .helmet = true }) == Region::Head);

    // Standard semantic armor categories.
    assert(EDArmor::Classify("Skyrim.esm", Slots({32}), SemanticFlags{ .cuirass = true }) == Region::BodyTorso);
    assert(EDArmor::Classify("Skyrim.esm", Slots({33}), SemanticFlags{ .gauntlets = true }) == Region::Hands);
    assert(EDArmor::Classify("Skyrim.esm", Slots({37}), SemanticFlags{ .boots = true }) == Region::Feet);

    // TAWOBA/TEWOBA are modular: their plugin-scoped slot meaning overrides
    // misleading vanilla ArmorCuirass/ArmorHelmet/etc. keywords.
    assert(EDArmor::Classify("The Amazing World of Bikini Armors REMASTERED.esp", Slots({52}), SemanticFlags{ .cuirass = true }) == Region::BodyPelvisLegs);
    assert(EDArmor::Classify("(Pumpkin)-TEWOBA-TheExpandedWorldofBikiniArmor.esp", Slots({57}), SemanticFlags{ .cuirass = true }) == Region::BodyShouldersBack);
    assert(EDArmor::Classify("The Amazing World of Bikini Armors REMASTERED.esp", Slots({46}), SemanticFlags{ .helmet = true }) == Region::BodyTorso);

    // Modular head/hands/feet and vanilla adjacent slots.
    assert(EDArmor::Classify("the amazing world of bikini armors remastered.esp", Slots({44}), {}) == Region::Head);
    assert(EDArmor::Classify("The Amazing World of Bikini Armors REMASTERED.esp", Slots({34}), {}) == Region::Hands);
    assert(EDArmor::Classify("The Amazing World of Bikini Armors REMASTERED.esp", Slots({38}), {}) == Region::Feet);

    // Auxiliary slots must not gain global anatomical meaning for unrelated mods.
    assert(EDArmor::Classify("SomeOtherArmor.esp", Slots({57}), {}) == Region::Unknown);

    // Vanilla slot fallback still works when useful keywords are absent.
    assert(EDArmor::Classify("SomeOtherArmor.esp", Slots({30}), {}) == Region::Head);
    assert(EDArmor::Classify("SomeOtherArmor.esp", Slots({32}), {}) == Region::BodyTorso);
    assert(EDArmor::Classify("SomeOtherArmor.esp", Slots({34}), {}) == Region::Hands);
    assert(EDArmor::Classify("SomeOtherArmor.esp", Slots({38}), {}) == Region::Feet);

    // Slot 60 remains intentionally unclassified unless another rule identifies it.
    assert(EDArmor::Classify("The Amazing World of Bikini Armors REMASTERED.esp", Slots({60}), {}) == Region::Unknown);

    return 0;
}
