#!/usr/bin/env python3
from pathlib import Path

SOURCE = Path("src/FoundEquipData.cpp")

HELPER = '''\nnamespace {\n    bool JM_IsLivingDwemerCuirass(RE::TESForm* form) {\n        if (!form)\n            return false;\n\n        static RE::TESObjectARMO* livingDwemerCuirass = []() -> RE::TESObjectARMO* {\n            auto* dataHandler = RE::TESDataHandler::GetSingleton();\n            return dataHandler\n                ? dataHandler->LookupForm<RE::TESObjectARMO>(0x80A, "DwarvenDeviousCuirass.esp")\n                : nullptr;\n        }();\n\n        return livingDwemerCuirass && form == livingDwemerCuirass;\n    }\n}\n'''

ANCHOR = '#include "Settings.h"\n'
PROCESS_OLD = '''bool FoundEquipData::CanProcessObject() {\n    if (!baseForm || IsUnarmed()) return false;\n\n    // Is a Weapon\n'''
PROCESS_NEW = '''bool FoundEquipData::CanProcessObject() {\n    if (!baseForm || IsUnarmed()) return false;\n\n    // JM: Host Reclamation owns the Living Cuirass lifecycle.\n    if (JM_IsLivingDwemerCuirass(baseForm)) return false;\n\n    // Is a Weapon\n'''
TEMPER_OLD = '''bool FoundEquipData::CanTemper() {\n    if (!baseForm || IsUnarmed()) return false;\n\n    // Do not effect Non-Playable items\n'''
TEMPER_NEW = '''bool FoundEquipData::CanTemper() {\n    if (!baseForm || IsUnarmed()) return false;\n\n    // JM: exact-form immunity. TemperDecay() cannot degrade this armor.\n    if (JM_IsLivingDwemerCuirass(baseForm)) return false;\n\n    // Do not effect Non-Playable items\n'''
BREAK_OLD = '''bool FoundEquipData::CanBreak() {\n\t// Run various checks to see if the item is breakable\n    if (!baseForm || !objectData)\n        return false;\n\n    // Already broken or unarmed\n'''
BREAK_NEW = '''bool FoundEquipData::CanBreak() {\n\t// Run various checks to see if the item is breakable\n    if (!baseForm || !objectData)\n        return false;\n\n    // JM: second exact-form guard if CanBreak() is called independently.\n    if (JM_IsLivingDwemerCuirass(baseForm)) return false;\n\n    // Already broken or unarmed\n'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one baseline match, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    if 'JM_IsLivingDwemerCuirass' in text:
        raise RuntimeError("Source is already or partially patched; refusing ambiguous baseline")
    if text.count(ANCHOR) != 1:
        raise RuntimeError("Settings include anchor mismatch")

    text = text.replace(ANCHOR, ANCHOR + HELPER, 1)
    text = replace_once(text, PROCESS_OLD, PROCESS_NEW, "CanProcessObject")
    text = replace_once(text, TEMPER_OLD, TEMPER_NEW, "CanTemper")
    text = replace_once(text, BREAK_OLD, BREAK_NEW, "CanBreak")
    SOURCE.write_text(text, encoding="utf-8", newline="\n")

    assert text.count('if (JM_IsLivingDwemerCuirass(baseForm)) return false;') == 3
    assert 'LookupForm<RE::TESObjectARMO>(0x80A, "DwarvenDeviousCuirass.esp")' in text
    print("Living Cuirass exact-form immunity applied and verified")


if __name__ == "__main__":
    main()
