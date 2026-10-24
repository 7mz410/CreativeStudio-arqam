#!/usr/bin/env python3
"""Apply the arqam (Creative Studio) branding on top of upstream GridCraft.

Only user-visible text is rebranded; crate names, the file format and other internals keep their
upstream names so `git merge upstream/main` stays easy. The script is idempotent: after merging
upstream, resolve any conflicts in favour of upstream and run it again.

    python3 studio/rebrand.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = 'arqam'
REPO = 'https://github.com/7mz410/CreativeStudio-arqam'
SITE = 'https://studio.creative.ps'
APP_SITE = 'https://arqam.studio.creative.ps'
# Persisted names and legal lines; renaming them would lose settings or misstate copyright.
KEEP = ('by the ArtCraft team', 'Application Support/GridCraft', '/roaming/GridCraft', 'the GridCraft authors', 'GridCraft contributors', 'GRIDCRAFT_')

# (file, upstream text, our text[, marker meaning "already applied"]). The upstream text may also
# be found in its renamed form (after the general rename below).
RULES = [
    # About and the Help menu: our links, no Discord.
    ('crates/ui-egui/src/dialogs.rs', '"A clean-room, open-source, Rust-native spreadsheet. Part of ArtCraft."',
     '"A clean-room, open-source, Rust-native spreadsheet. Part of the Creative Studio suite, built on GridCraft by the ArtCraft team."'),
    ('crates/ui-egui/src/dialogs.rs', 'ui.hyperlink_to("getartcraft.com/apps/gridcraft", "https://getartcraft.com/apps/gridcraft");',
     f'ui.hyperlink_to("arqam.studio.creative.ps", "{APP_SITE}");'),
    ('crates/ui-egui/src/dialogs.rs', 'ui.hyperlink_to("Join the ArtCraft Discord", "https://discord.gg/artcraft");',
     f'ui.hyperlink_to("Source code: github.com/7mz410/CreativeStudio-arqam", "{REPO}");'),
    ('apps/gridcraft/src/native_menu.rs', '("GridCraft on getartcraft.com", "url:https://getartcraft.com/apps/gridcraft", None),',
     f'("arqam on studio.creative.ps", "url:{APP_SITE}", None),'),
    ('apps/gridcraft/src/native_menu.rs', '("Join the ArtCraft Discord…", "url:https://discord.gg/artcraft", None),',
     f'("Creative Studio…", "url:{SITE}", None),'),
    # Web page and packages.
    ('apps/gridcraft-web/index.html', '<title>GridCraft</title>', f'<title>{NAME}</title>'),
    ('apps/gridcraft-web/index.html', 'Loading GridCraft&hellip;', f'Loading {NAME}&hellip;', 'ss-scene'),  # or the splash
    ('packaging/macos/Info.plist.in', '<string>ai.storyteller.gridcraft</string>', '<string>ps.creative.studio.arqam</string>'),
    ('packaging/windows/gridcraft.wxs', '<Property Id="ARPURLINFOABOUT" Value="https://getartcraft.com/apps/gridcraft" />', f'<Property Id="ARPURLINFOABOUT" Value="{APP_SITE}" />'),
    ('packaging/windows/gridcraft.wxs', '<Property Id="ARPURLUPDATEINFO" Value="https://getartcraft.com/apps/gridcraft" />', f'<Property Id="ARPURLUPDATEINFO" Value="{REPO}/releases" />'),
    ('packaging/windows/gridcraft.wxs', '<Property Id="ARPHELPLINK" Value="https://discord.gg/artcraft" />', f'<Property Id="ARPHELPLINK" Value="{REPO}/issues" />'),
    ('packaging/linux/nfpm.yaml', 'homepage: https://getartcraft.com/apps/gridcraft', f'homepage: {APP_SITE}'),
    # Arabic interface and font fallback (Creative Studio).
    ('crates/ui-egui/Cargo.toml',
     'image = { workspace = true }\nskrifa = { workspace = true }',
     'image = { workspace = true }\nskrifa = { workspace = true }\nunicode-bidi = "0.3.18"',
     'unicode-bidi'),
    ('ATTRIBUTION.md',
     '| `assets/app-icon/LICENSE.txt` | Hamza Abu Ayyash (Creative Studio) | the arqam star (`docs/studio/arqam.svg`) on a navy tile, rendered by `packaging/icons.sh` | MIT OR Apache-2.0 | App icon (see `assets/app-icon/README.md`) |',
     '| `assets/app-icon/LICENSE.txt` | Hamza Abu Ayyash (Creative Studio) | the arqam star (`docs/studio/arqam.svg`) on a navy tile, rendered by `packaging/icons.sh` | MIT OR Apache-2.0 | App icon (see `assets/app-icon/README.md`) |\n| `assets/fonts/IBMPlexSansArabic-Regular.ttf` | IBM Corp. (Mike Abbink, Bold Monday) | https://github.com/google/fonts/tree/main/ofl/ibmplexsansarabic | OFL-1.1 (`assets/fonts/OFL-IBMPlexSansArabic.txt`) | Creative Studio: Arabic UI font |\n| `assets/fonts/IBMPlexSansArabic-SemiBold.ttf` | IBM Corp. (Mike Abbink, Bold Monday) | https://github.com/google/fonts/tree/main/ofl/ibmplexsansarabic | OFL-1.1 (`assets/fonts/OFL-IBMPlexSansArabic.txt`) | Creative Studio: Arabic UI font |\n| `assets/fonts/OFL-IBMPlexSansArabic.txt` | (licence text) | upstream project | — |  |',
     'IBMPlexSansArabic'),
    ('crates/ui-egui/src/theme.rs',
     '''    let mut fonts = FontDefinitions::default();
    let base_prop: Vec<String> = fonts.families.get(&FontFamily::Proportional).cloned().unwrap_or_default();
    let base_mono: Vec<String> = fonts.families.get(&FontFamily::Monospace).cloned().unwrap_or_default();
    let mut bound: Vec<String> = Vec::new();
    // The non-Latin fallback faces have to sit at the end of each chain: a Latin font owns Latin,
    // and epaint picks the first face that has the glyph, so they only catch their own scripts.
    let fallback = load_fallback(&mut fonts, HanOrder::of(language));
    for role in [UI, UI_BOLD, CELL, CELL_BOLD, CELL_ITALIC, CELL_BOLD_ITALIC, SERIF, MONO] {
        let paths = candidates(role);
        let refs: Vec<(&str, u32)> = paths.iter().map(|(p, i)| (p.as_str(), *i)).collect();
        let mut chain: Vec<String> = Vec::new();
        if let Some(fd) = try_load(&refs) {
            let key = format!("sys-{role}");
            fonts.font_data.insert(key.clone(), Arc::new(fd));
            chain.push(key);
        } else if role == UI_BOLD {
            chain.push(format!("sys-{UI}"));
        } else if role.starts_with("cell-") {
            chain.push(format!("sys-{CELL}"));
        }
        chain.extend(if role == MONO { base_mono.clone() } else { base_prop.clone() });
        chain.extend(fallback.iter().cloned());''',
     '''    let mut fonts = FontDefinitions::default();
    let base_prop: Vec<String> = fonts.families.get(&FontFamily::Proportional).cloned().unwrap_or_default();
    let base_mono: Vec<String> = fonts.families.get(&FontFamily::Monospace).cloned().unwrap_or_default();
    let mut bound: Vec<String> = Vec::new();
    fonts.font_data.insert(
        "IBMPlexSansArabic".to_string(),
        Arc::new(FontData::from_static(include_bytes!("../../../assets/fonts/IBMPlexSansArabic-Regular.ttf"))),
    );
    fonts.font_data.insert(
        "IBMPlexSansArabic-SemiBold".to_string(),
        Arc::new(FontData::from_static(include_bytes!("../../../assets/fonts/IBMPlexSansArabic-SemiBold.ttf"))),
    );
    // The non-Latin fallback faces have to sit at the end of each chain: a Latin font owns Latin,
    // and epaint picks the first face that has the glyph, so they only catch their own scripts.
    let fallback = load_fallback(&mut fonts, HanOrder::of(language));
    for role in [UI, UI_BOLD, CELL, CELL_BOLD, CELL_ITALIC, CELL_BOLD_ITALIC, SERIF, MONO] {
        let paths = candidates(role);
        let refs: Vec<(&str, u32)> = paths.iter().map(|(p, i)| (p.as_str(), *i)).collect();
        let mut chain: Vec<String> = Vec::new();
        if let Some(fd) = try_load(&refs) {
            let key = format!("sys-{role}");
            fonts.font_data.insert(key.clone(), Arc::new(fd));
            chain.push(key);
        } else if role == UI_BOLD {
            chain.push(format!("sys-{UI}"));
        } else if role.starts_with("cell-") {
            chain.push(format!("sys-{CELL}"));
        }
        chain.extend(if role == MONO { base_mono.clone() } else { base_prop.clone() });
        let arabic = if role == UI_BOLD || role == CELL_BOLD || role == CELL_BOLD_ITALIC {
            "IBMPlexSansArabic-SemiBold"
        } else {
            "IBMPlexSansArabic"
        };
        chain.push(arabic.to_string());
        chain.extend(fallback.iter().cloned());''',
     'IBMPlexSansArabic'),
    ('crates/ui-egui/src/i18n.rs',
     'mod cs;\nmod de;\nmod es;\nmod fr;\nmod ko;\nmod pt;\nmod ru;\nmod zh;',
     'mod ar;\npub(crate) mod bidi;\nmod cs;\nmod de;\nmod es;\nmod fr;\nmod ko;\nmod pt;\nmod ru;\nmod zh;',
     'pub(crate) mod bidi;'),
    ('crates/ui-egui/src/i18n.rs',
     '    #[serde(rename = "pt")]\n    PtBr,\n    De,\n    Cs,\n    Fr,\n}',
     '    #[serde(rename = "pt")]\n    PtBr,\n    De,\n    Cs,\n    Fr,\n    Ar,\n}',
     '    Fr,\n    Ar,'),
    ('crates/ui-egui/src/i18n.rs',
     'pub const ALL: [Self; 19] = [',
     'pub const ALL: [Self; 20] = [',
     '        Self::Fr,\n        Self::Ar,'),
    ('crates/ui-egui/src/i18n.rs',
     '            Self::Cs => "Čeština",\n            Self::Fr => "Français",\n        }',
     '            Self::Cs => "Čeština",\n            Self::Fr => "Français",\n            Self::Ar => "العربية",\n        }',
     'Self::Ar => "العربية"'),
    ('crates/ui-egui/src/i18n.rs',
     '            Self::Cs => "cs",\n            Self::Fr => "fr",\n        }',
     '            Self::Cs => "cs",\n            Self::Fr => "fr",\n            Self::Ar => "ar",\n        }',
     'Self::Ar => "ar"'),
    ('crates/ui-egui/src/i18n.rs',
     '            "cs" => Some(Self::Cs),\n            "fr" => Some(Self::Fr),\n            _ => None,',
     '            "cs" => Some(Self::Cs),\n            "fr" => Some(Self::Fr),\n            "ar" => Some(Self::Ar),\n            _ => None,',
     '"ar" => Some(Self::Ar)'),
    ('crates/ui-egui/src/i18n.rs',
     '            Self::Cs => cs::translate(text),\n            Self::Fr => fr::translate(text),\n        };',
     '            Self::Cs => cs::translate(text),\n            Self::Fr => fr::translate(text),\n            Self::Ar => ar::translate(text),\n        };',
     'Self::Ar => ar::translate(text)'),
    ('crates/ui-egui/src/i18n.rs',
     '''        assert_eq!(Language::from_tag("fr-FR"), Some(Language::Fr));
        assert_eq!(Language::from_tag("fr_CA"), Some(Language::Fr));
        assert_eq!(Language::parse("fr"), Some(Language::Fr));
    }''',
     '''        assert_eq!(Language::from_tag("fr-FR"), Some(Language::Fr));
        assert_eq!(Language::from_tag("fr_CA"), Some(Language::Fr));
        assert_eq!(Language::parse("fr"), Some(Language::Fr));
        assert_eq!(Language::from_tag("ar-SA"), Some(Language::Ar));
        assert_eq!(Language::parse("ar"), Some(Language::Ar));
    }

    #[test]
    fn arabic_translates_labels() {
        assert_eq!(Language::Ar.tr("New"), "جديد");
        assert_eq!(Language::Ar.tr("File"), "ملف");
        assert_eq!(Language::Ar.tr("Save"), "حفظ");
        assert_eq!(Language::Ar.tr("Wrap Text"), crate::i18n::bidi::visual("التفاف النص"));
    }''',
     'arabic_translates_labels'),
    ('crates/ui-egui/src/i18n/fr.rs',
     '        "Footer" => "Feuille de\\nprévision",',
     '        "Footer" => "Feuille de\\nprévision",\n        "Different First Page" => "Première page différente",\n        "Different Odd & Even Pages" => "Pages paires et impaires différentes",',
     'Première page différente'),
]
# Text in string literals and catalogs, before the general rename.
LITERALS = []
STRING = re.compile(r'"(?:[^"\\\n]|\\.)*"')


def rename(lit: str) -> str:
    for a, b in LITERALS:
        lit = lit.replace(a, b)
    if any(k in lit for k in KEEP):
        return lit
    return lit.replace('GridCraft', NAME)


def renamed_code(text: str) -> str:
    return STRING.sub(lambda m: rename(m.group(0)), text)


def apply_rules() -> list:
    changed = []
    for rel, a, b, *marker in RULES:
        p = ROOT / rel
        s = p.read_text(encoding='utf-8')
        if marker and marker[0] in s:
            continue
        if a not in s and renamed_code(a) in s:
            a = renamed_code(a)  # the general rename got there first
        if a not in s or (b and a in b and b in s):
            if not b or b in s or renamed_code(b) in s:
                continue  # already applied
            print(f'warning: {rel}: upstream text not found (did upstream change it?): {a[:70]!r}')
            continue
        p.write_text(s.replace(a, b), encoding='utf-8')
        changed.append(rel)
    return changed


def rename_sources() -> list:
    changed = []
    for p in sorted((ROOT / 'crates/ui-egui').rglob('*.rs')) + [q for q in sorted((ROOT / 'crates/engine').rglob('*.rs')) if not q.name.startswith('tests')] + sorted((ROOT / 'apps').rglob('*.rs')):
        s = p.read_text(encoding='utf-8')
        o = renamed_code(s)
        if o != s:
            p.write_text(o, encoding='utf-8')
            changed.append(p.relative_to(ROOT).as_posix())
    # Catalog rows are `context<TAB>English<TAB>translation`: rename both text columns alike.
    for p in sorted((ROOT / 'crates/ui-egui/src/i18n').glob('*.tsv')):
        s = p.read_text(encoding='utf-8')
        rows = []
        for line in s.split('\n'):
            cells = line.split('\t')
            if len(cells) >= 3 and not line.startswith('#'):
                line = '\t'.join([cells[0], *(rename(c) for c in cells[1:])])
            rows.append(line)
        o = '\n'.join(rows)
        if o != s:
            p.write_text(o, encoding='utf-8')
            changed.append(p.relative_to(ROOT).as_posix())
    plist = ROOT / 'packaging/macos/Info.plist.in'
    s = plist.read_text(encoding='utf-8')
    o = re.sub(r'(<key>CFBundle(?:Display|Executable)?Name</key>\s*<string>)GridCraft(</string>)', rf'\g<1>{NAME}\2', s)
    if o != s:
        plist.write_text(o, encoding='utf-8')
        changed.append('packaging/macos/Info.plist.in')
    return changed


def main():
    changed = apply_rules() + rename_sources()
    for c in sorted(set(changed)):
        print('rebranded', c)


# Creative Studio: the macOS app folder in the .dmg and the volume name carry our name
# (packaging/macos/package.sh). Bundle and binary names inside the package stay as upstream has them.
PACKAGING_NAMES = {
    'packaging/macos/package.sh': [
        ('GridCraft.app', 'arqam.app'),
        ('-volname "GridCraft"', '-volname "arqam"'),
        ('-hfs-volume-name "GridCraft"', '-hfs-volume-name "arqam"'),
    ],
}


def apply_packaging_names() -> list:
    changed = []
    for rel, pairs in PACKAGING_NAMES.items():
        path = ROOT / rel
        src = path.read_text(encoding='utf-8')
        out = src
        for a, b in pairs:
            out = out.replace(a, b)
        if out != src:
            path.write_text(out, encoding='utf-8')
            changed.append(path)
    return changed


if __name__ == '__main__':
    main()
    for _p in apply_packaging_names():
        print('rebranded', _p.relative_to(ROOT))
