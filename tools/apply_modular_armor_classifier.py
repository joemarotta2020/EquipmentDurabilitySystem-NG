#!/usr/bin/env python3
from pathlib import Path

FOUND = Path("src/FoundEquipData.cpp")
EVENTS = Path("src/Events.cpp")

FOUND_INCLUDE = '#include "Settings.h"\n'
FOUND_INCLUDE_NEW = '#include "Settings.h"\n#include "ArmorClassifier.h"\n'

OLD_EQUIPMENT_TYPE = '''EquipmentType FoundEquipData::GetEquipmentType() {
\tif (baseForm->IsWeapon())
        return EquipmentType::Weapon;

\telse if (auto* armor = baseForm->As<RE::TESObjectARMO>()) {
\t\tauto hasSlot = [&](auto... slots){ return (... || armor->HasPartOf(slots)); };

        if (hasSlot(RE::BGSBipedObjectForm::BipedObjectSlot::kBody,
                RE::BGSBipedObjectForm::BipedObjectSlot::kTail))
            return EquipmentType::Body;

        else if (hasSlot(RE::BGSBipedObjectForm::BipedObjectSlot::kHead,
                RE::BGSBipedObjectForm::BipedObjectSlot::kHair,
                RE::BGSBipedObjectForm::BipedObjectSlot::kLongHair)) 
            return EquipmentType::Head;

        else if (hasSlot(RE::BGSBipedObjectForm::BipedObjectSlot::kHands,
                RE::BGSBipedObjectForm::BipedObjectSlot::kForearms))
            return EquipmentType::Hand;

        else if (hasSlot(RE::BGSBipedObjectForm::BipedObjectSlot::kFeet,
                RE::BGSBipedObjectForm::BipedObjectSlot::kCalves))
            return EquipmentType::Foot;

        else if (hasSlot(RE::BGSBipedObjectForm::BipedObjectSlot::kShield)) 
            return EquipmentType::Shield;
\t}

\treturn EquipmentType::None;
}
'''

NEW_EQUIPMENT_TYPE = '''EquipmentType FoundEquipData::GetEquipmentType() {
    if (baseForm->IsWeapon())
        return EquipmentType::Weapon;

    if (auto* armor = baseForm->As<RE::TESObjectARMO>()) {
        if (armor->IsShield())
            return EquipmentType::Shield;

        switch (EDArmor::ClassifyArmor(armor)) {
        case EDArmor::Region::Head:
            return EquipmentType::Head;
        case EDArmor::Region::Hands:
            return EquipmentType::Hand;
        case EDArmor::Region::Feet:
            return EquipmentType::Foot;
        case EDArmor::Region::BodyTorso:
        case EDArmor::Region::BodyPelvisLegs:
        case EDArmor::Region::BodyShouldersBack:
            return EquipmentType::Body;
        default:
            break;
        }
    }

    return EquipmentType::None;
}
'''

ARMOR_FUNCTION_END = '''    return equipData;
}
'''

CLASSIFIED_FUNCTION = '''

std::vector<ClassifiedArmorData> FindEquippedArmorByRegion(RE::InventoryChanges* a_Changes) {
    std::vector<ClassifiedArmorData> result;
    if (!a_Changes || !a_Changes->entryList)
        return result;

    for (const auto& entry : *a_Changes->entryList) {
        if (!entry || !entry->extraLists)
            continue;

        auto* armor = entry->GetObject()->As<RE::TESObjectARMO>();
        if (!armor || armor->IsShield())
            continue;

        const auto region = EDArmor::ClassifyArmor(armor);
        if (region == EDArmor::Region::Unknown)
            continue;

        auto extraIt = std::find_if(entry->extraLists->begin(), entry->extraLists->end(), [](const RE::ExtraDataList* extra) {
            return extra && (extra->HasType(RE::ExtraDataType::kWorn) || extra->HasType(RE::ExtraDataType::kWornLeft));
        });
        if (extraIt == entry->extraLists->end())
            continue;

        FoundEquipData equipment(entry->GetObject(), *extraIt);
        equipment.refForm = entry->GetObject();

        // Eligibility is resolved before weighting so an undamageable piece
        // cannot consume a durability event or prevent category renormalization.
        if (!equipment.CanTemper())
            continue;

        result.push_back({ equipment, region });
    }

    return result;
}
'''

OLD_WEIGHTED = '''static void DecayWeightedArmorPiece(RE::Actor* actor, RE::InventoryChanges* changes, bool powerAttack) {
\t// JM Pass 1: weighted body-region targeting. Empty regions are omitted from
\t// the total, so the configured weights automatically renormalize across the
\t// armor/clothing that is actually equipped.
\tconstexpr int kBodyWeight = 50;
\tconstexpr int kHeadWeight = 15;
\tconstexpr int kHandsWeight = 15;
\tconstexpr int kFeetWeight = 20;

\tFoundEquipData body = FindEquippedArmor(changes, RE::BGSBipedObjectForm::BipedObjectSlot::kBody);

\tFoundEquipData head = FindEquippedArmor(changes, RE::BGSBipedObjectForm::BipedObjectSlot::kHead);
\tif (!head.baseForm)
\t\thead = FindEquippedArmor(changes, RE::BGSBipedObjectForm::BipedObjectSlot::kHair);

\tFoundEquipData hands = FindEquippedArmor(changes, RE::BGSBipedObjectForm::BipedObjectSlot::kHands);
\tFoundEquipData feet = FindEquippedArmor(changes, RE::BGSBipedObjectForm::BipedObjectSlot::kFeet);

\tint totalWeight = 0;
\tif (body.baseForm) totalWeight += kBodyWeight;
\tif (head.baseForm) totalWeight += kHeadWeight;
\tif (hands.baseForm) totalWeight += kHandsWeight;
\tif (feet.baseForm) totalWeight += kFeetWeight;
\tif (totalWeight <= 0) return;

\tint roll = Random::Int(1, totalWeight);

\tauto select = [&](FoundEquipData& armor, int weight) {
\t\tif (!armor.baseForm) return false;
\t\tif (roll <= weight) {
\t\t\tTemperDecay(&armor, actor, powerAttack);
\t\t\treturn true;
\t\t}
\t\troll -= weight;
\t\treturn false;
\t};

\tif (select(body, kBodyWeight)) return;
\tif (select(head, kHeadWeight)) return;
\tif (select(hands, kHandsWeight)) return;
\tselect(feet, kFeetWeight);
}
'''

NEW_WEIGHTED = '''static void DecayWeightedArmorPiece(RE::Actor* actor, RE::InventoryChanges* changes, bool powerAttack) {
    constexpr int kBodyWeight = 50;
    constexpr int kHeadWeight = 15;
    constexpr int kHandsWeight = 15;
    constexpr int kFeetWeight = 20;

    constexpr int kTorsoWeight = 45;
    constexpr int kPelvisLegsWeight = 35;
    constexpr int kShouldersBackWeight = 20;

    auto equipped = FindEquippedArmorByRegion(changes);
    if (equipped.empty())
        return;

    std::vector<FoundEquipData*> head;
    std::vector<FoundEquipData*> hands;
    std::vector<FoundEquipData*> feet;
    std::vector<FoundEquipData*> torso;
    std::vector<FoundEquipData*> pelvisLegs;
    std::vector<FoundEquipData*> shouldersBack;

    for (auto& item : equipped) {
        switch (item.region) {
        case EDArmor::Region::Head:
            head.push_back(&item.equipment);
            break;
        case EDArmor::Region::Hands:
            hands.push_back(&item.equipment);
            break;
        case EDArmor::Region::Feet:
            feet.push_back(&item.equipment);
            break;
        case EDArmor::Region::BodyTorso:
            torso.push_back(&item.equipment);
            break;
        case EDArmor::Region::BodyPelvisLegs:
            pelvisLegs.push_back(&item.equipment);
            break;
        case EDArmor::Region::BodyShouldersBack:
            shouldersBack.push_back(&item.equipment);
            break;
        default:
            break;
        }
    }

    auto decayRandom = [&](std::vector<FoundEquipData*>& candidates) {
        if (candidates.empty())
            return false;
        const int index = Random::Int(0, static_cast<int>(candidates.size()) - 1);
        TemperDecay(candidates[static_cast<std::size_t>(index)], actor, powerAttack);
        return true;
    };

    auto decayBody = [&]() {
        int total = 0;
        if (!torso.empty()) total += kTorsoWeight;
        if (!pelvisLegs.empty()) total += kPelvisLegsWeight;
        if (!shouldersBack.empty()) total += kShouldersBackWeight;
        if (total <= 0)
            return false;

        int roll = Random::Int(1, total);
        if (!torso.empty()) {
            if (roll <= kTorsoWeight)
                return decayRandom(torso);
            roll -= kTorsoWeight;
        }
        if (!pelvisLegs.empty()) {
            if (roll <= kPelvisLegsWeight)
                return decayRandom(pelvisLegs);
            roll -= kPelvisLegsWeight;
        }
        return decayRandom(shouldersBack);
    };

    const bool hasBody = !torso.empty() || !pelvisLegs.empty() || !shouldersBack.empty();
    int totalWeight = 0;
    if (hasBody) totalWeight += kBodyWeight;
    if (!head.empty()) totalWeight += kHeadWeight;
    if (!hands.empty()) totalWeight += kHandsWeight;
    if (!feet.empty()) totalWeight += kFeetWeight;
    if (totalWeight <= 0)
        return;

    int roll = Random::Int(1, totalWeight);
    if (hasBody) {
        if (roll <= kBodyWeight) {
            decayBody();
            return;
        }
        roll -= kBodyWeight;
    }
    if (!head.empty()) {
        if (roll <= kHeadWeight) {
            decayRandom(head);
            return;
        }
        roll -= kHeadWeight;
    }
    if (!hands.empty()) {
        if (roll <= kHandsWeight) {
            decayRandom(hands);
            return;
        }
        roll -= kHandsWeight;
    }
    decayRandom(feet);
}
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one baseline match, found {count}")
    return text.replace(old, new, 1)


def patch_found() -> None:
    text = FOUND.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    if "FindEquippedArmorByRegion" in text or '#include "ArmorClassifier.h"' in text:
        raise RuntimeError("FoundEquipData.cpp is already or partially classifier-patched")

    text = replace_once(text, FOUND_INCLUDE, FOUND_INCLUDE_NEW, "ArmorClassifier include")
    text = replace_once(text, OLD_EQUIPMENT_TYPE, NEW_EQUIPMENT_TYPE, "GetEquipmentType")

    # The final FindEquippedArmor function ends at EOF in the current baseline.
    if not text.endswith(ARMOR_FUNCTION_END):
        raise RuntimeError("FindEquippedArmor EOF anchor mismatch")
    text = text + CLASSIFIED_FUNCTION

    FOUND.write_text(text, encoding="utf-8", newline="\n")


def patch_events() -> None:
    text = EVENTS.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    if "kPelvisLegsWeight" in text:
        raise RuntimeError("Events.cpp is already or partially classifier-patched")
    text = replace_once(text, OLD_WEIGHTED, NEW_WEIGHTED, "DecayWeightedArmorPiece")
    EVENTS.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    patch_found()
    patch_events()

    found = FOUND.read_text(encoding="utf-8")
    events = EVENTS.read_text(encoding="utf-8")
    assert "EDArmor::ClassifyArmor" in found
    assert "FindEquippedArmorByRegion" in found
    assert "kTorsoWeight = 45" in events
    assert "kPelvisLegsWeight = 35" in events
    assert "kShouldersBackWeight = 20" in events
    print("Modular/semantic armor classifier integration applied and verified")


if __name__ == "__main__":
    main()
