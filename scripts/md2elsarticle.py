"""Convert docs/paper/manuscript.md and supplementary.md to Elsevier elsarticle LaTeX.

The markdown files remain the single source; this script writes
docs/paper/latex/{manuscript,supplementary}.tex (author-year, elsarticle-harv).

    python scripts/md2elsarticle.py && cd docs/paper/latex && latexmk -pdf manuscript supplementary
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "docs" / "paper"
OUT = PAPER / "latex"
FIGDIR = "../../../figures/paper/"

# (first-author surname, year) -> bib key
CITE = {
    ("Angelopoulos", "2024"): "angelopoulos2024crc", ("Angelopoulos", "2025"): "angelopoulos2025ltt",
    ("Azaïs", "2009"): "azais2009", ("Barber", "2023"): "barber2023", ("Booton", "1954"): "booton1954",
    ("Campi", "2008"): "campi2008", ("Diquigiovanni", "2022"): "diquigiovanni2022", ("Dunn", "2023"): "dunn2023",
    ("European Space Agency", "2021"): "esa2021", ("Everett", "n.d."): "everett_demo5", ("FAO", "2025"): "fao2025",
    ("Galceran", "2013"): "galceran2013", ("Hall", "1979"): "hall1979", ("Hameed", "2016"): "hameed2016",
    ("Hewing", "2020"): "hewing2020", ("Höffmann", "2024"): "hoffmann2024", ("Kazakov", "1956"): "kazakov1956",
    ("Leadbetter", "1983"): "leadbetter1983", ("Lei", "2015"): "lei2015", ("Lenain", "2006"): "lenain2006",
    ("Li", "2002"): "li2002", ("Lindemann", "2023"): "lindemann2023", ("Mayne", "2005"): "mayne2005",
    ("Mier", "2023"): "mier2023", ("Mier", "2025"): "mier2025", ("Mohajerin Esfahani", "2018"): "mohajerin2018",
    ("NOAA", "n.d."): "noaacors", ("Pannocchia", "2003"): "pannocchia2003", ("Piterbarg", "1996"): "piterbarg1996",
    ("Rice", "1944"): "rice1944", ("Romano", "2019"): "romano2019", ("Sun", "2023"): "sun2023",
    ("Takasu", "2009"): "takasu2009", ("Teng", "2023"): "teng2023", ("Tang", "2022"): "tang2022", ("Tibshirani", "2019"): "tibshirani2019",
    ("Vovk", "2012"): "vovk2012", ("Wang", "2025"): "wang2025", ("Wu", "2023"): "wu2023",
    ("Zhang", "2015"): "zhang2015", ("Zhang", "2021"): "zhang2021", ("Zhao", "2024"): "zhao2024",
}
NAME = r"(?:European Space Agency|Mohajerin Esfahani|[A-Z][\w'ïöé-]+)(?: and (?:[A-Z][\w-]+ )*[A-Z][\w-]+| et al\.)?"
YEARS = r"(?:(?:19|20)\d\d|n\.d\.)(?:, (?:19|20)\d\d)*"
ITEM = re.compile(rf"({NAME}), ({YEARS})")
NARR = re.compile(rf"({NAME}) \(({YEARS})\)")
used_keys = set()


def keys(name, years):
    first = name.split(" and ")[0].replace(" et al.", "")
    out = []
    for y in years.split(", "):
        k = CITE.get((first, y))
        if k is None:
            raise KeyError(f"no bib key for {first} {y}")
        used_keys.add(k)
        out.append(k)
    return out


def cite_paren(m):
    body = m.group(1)
    items = list(ITEM.finditer(body))
    if not items:
        return m.group(0)
    # every citation must sit at the end of the parenthesis, separated by "; "
    tail = body[items[0].start():]
    if re.sub(ITEM, "", tail).replace("; ", "").strip():
        return m.group(0)
    pre = body[:items[0].start()].strip()
    ks = [k for it in items for k in keys(it.group(1), it.group(2))]
    opt = f"[{md_inline([pre])[0]}][]" if pre else ""
    return stash(rf"\citep{opt}{{{','.join(ks)}}}")


def cites(text):
    text = re.sub(r"\(([^()]*)\)", cite_paren, text)
    return NARR.sub(lambda m: stash(rf"\citet{{{','.join(keys(m.group(1), m.group(2)))}}}"), text)


STASH = []


def stash(tex):
    STASH.append(tex)
    return f"ZZCITE{len(STASH) - 1}ZZ"


def unstash(tex):
    return re.sub(r"ZZCITE(\d+)ZZ", lambda m: STASH[int(m.group(1))], tex)


# --------------------------------------------------------------------------- pandoc for inline fragments
SEP = "ZZSEPZZ"
SINGLE_COL = {"fig_information_limit"}  # drawn at 90 mm


def md_inline(frags):
    """Convert many markdown fragments to LaTeX with one pandoc call."""
    if not frags:
        return []
    src = f"\n\n{SEP}\n\n".join(f if f.strip() else "~" for f in frags)
    tex = subprocess.run(["pandoc", "-f", "markdown-auto_identifiers", "-t", "latex", "--wrap=none"],
                         input=src, capture_output=True, text=True, check=True).stdout
    parts = [p.strip() for p in tex.split(SEP)]
    assert len(parts) == len(frags), (len(parts), len(frags))
    return [("" if p == "~" else p) for p in parts]


# --------------------------------------------------------------------------- blocks
def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    cells, cur, math = [], "", False
    for ch in line:
        if ch == "$":
            math = not math
        if ch == "|" and not math:
            cells.append(cur.strip())
            cur = ""
        else:
            cur += ch
    cells.append(cur.strip())
    return cells


def visible_len(s):
    s = re.sub(r"\$[^$]*\$", "xxxx", s)
    s = re.sub(r"[*`]", "", s)
    return len(s) + sum(1 for ch in s if ord(ch) > 0x2e80)  # CJK characters are two Latin widths


class Doc:
    """Parse markdown into a list of blocks; tables and figures become raw LaTeX later."""

    def __init__(self, md, supp):
        self.supp = supp
        self.blocks = []  # (kind, payload)
        lines = md.split("\n")
        i = 0
        while i < len(lines):
            ln = lines[i]
            if ln.startswith("<!--"):
                while "-->" not in lines[i]:
                    i += 1
                i += 1
                continue
            if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|?\s*$", lines[i + 1]):
                rows = [split_row(ln)]
                i += 2
                while i < len(lines) and lines[i].startswith("|"):
                    rows.append(split_row(lines[i]))
                    i += 1
                cap = None
                j = i
                while j < len(lines) and not lines[j].strip():
                    j += 1
                m = re.match(r"^\*Table (S?[0-9]+[a-z]?)\. (.*)\*\s*$", lines[j]) if j < len(lines) else None
                if m:
                    cap = (m.group(1), m.group(2))
                    i = j + 1
                self.blocks.append(("table", (rows, cap)))
                continue
            m = re.match(r"^!\[[^\]]*\]\(([^)]+)\)", ln)
            if m:
                path = Path(m.group(1)).stem
                j = i + 1
                while not lines[j].strip():
                    j += 1
                mc = re.match(r"^\*\*Fig\. (S?[0-9]+)\.\*\* (.*)$", lines[j])
                assert mc, lines[j]
                self.blocks.append(("figure", (path, mc.group(1), mc.group(2))))
                i = j + 1
                continue
            m = re.match(r"^(#{7,}) (.*)$", ln)
            if m:
                self.blocks.append(("md", f"**{m.group(2)}**"))
                i += 1
                continue
            self.blocks.append(("md", ln))
            i += 1

    def render(self):
        # collect fragments for one pandoc call
        frags = []
        for kind, p in self.blocks:
            if kind == "table":
                rows, cap = p
                frags += [c for r in rows for c in r] + ([cap[1]] if cap else [])
            elif kind == "figure":
                frags.append(p[2])
        conv = iter(md_inline([cites(f) for f in frags]))
        out_md, raw = [], []
        for kind, p in self.blocks:
            if kind == "md":
                out_md.append(p)
                continue
            if kind == "table":
                rows, cap = p
                trows = [[next(conv) for _ in r] for r in rows]
                tcap = (cap[0], next(conv)) if cap else None
                raw.append(self.table_tex(rows, trows, tcap))
            else:
                path, num, _ = p
                raw.append(self.figure_tex(path, num, next(conv)))
            out_md.append(f"\n{SEP}RAW{len(raw) - 1}\n")
        body = "\n".join(out_md)
        body = cites(body)
        tex = subprocess.run(["pandoc", "-f", "markdown-auto_identifiers", "-t", "latex", "--wrap=preserve",
                              "--top-level-division=section"],
                             input=body, capture_output=True, text=True, check=True).stdout
        tex = re.sub(rf"{SEP}RAW(\d+)", lambda m: raw[int(m.group(1))], tex)
        return unstash(tex)

    def label(self, kind, num):
        return f"{kind}:{num}"

    def caption(self, kind, num, text):
        if self.supp:  # supplementary numbers are fixed (S1, S5a, ...)
            cmd = r"\thetable" if kind == "tab" else r"\thefigure"
            return rf"\renewcommand{{{cmd}}}{{{num}}}\caption{{{text}}}"
        return rf"\caption{{{text}}}\label{{{self.label(kind, num)}}}"

    def table_tex(self, rows, trows, cap):
        ncol = max(len(r) for r in rows)
        trows = [r + [""] * (ncol - len(r)) for r in trows]
        maxlen = [max(visible_len(r[c]) if c < len(r) else 0 for r in rows) for c in range(ncol)]
        size = r"\footnotesize" if ncol <= 7 else r"\scriptsize"
        head = " & ".join(rf"\textbf{{{c}}}" if c else "" for c in trows[0]) + r" \\"
        body = "\n".join(" & ".join(r) + r" \\" for r in trows[1:])
        # natural-width tabular; long columns wrap at a width proportional to their text, and the whole
        # table is shrunk only if it is still wider than the text block
        em = 0.52 if ncol <= 7 else 0.5
        bodylen = [max([visible_len(r[c]) for r in rows[1:] if c < len(r)] or [0]) for c in range(ncol)]
        headlen = [visible_len(rows[0][c]) if c < len(rows[0]) else 0 for c in range(ncol)]
        spec = ""
        nats = [max(bodylen[c], min(headlen[c], 14)) for c in range(ncol)]
        wrap = [headlen[c] > nats[c] or nats[c] > 24 for c in range(ncol)]
        for c in range(ncol):
            if wrap[c]:  # wrap the header, or a long text column
                spec += rf">{{\raggedright\arraybackslash}}p{{{min(nats[c], 40) * em:.1f}em}}"
            else:
                spec += "l"
        # too wide for the text block: wrap columns share the remaining width (tabularx) instead of shrinking type
        total = sum(min(nats[c], 40) * em if wrap[c] else nats[c] * em * 0.95 + 0.8 for c in range(ncol))
        lw = sum(nats[c] * em * 0.95 + 0.8 for c in range(ncol) if not wrap[c])
        use_x = len(rows) <= 32 and any(wrap) and total > 46 and 46 - lw >= 7 * sum(wrap)
        if use_x:
            wsum = sum(min(nats[c], 40) for c in range(ncol) if wrap[c])
            nx = sum(wrap)
            spec = "".join(rf">{{\raggedright\arraybackslash\hsize={nx * min(nats[c], 40) / wsum:.2f}\hsize}}X"
                           if wrap[c] else "l" for c in range(ncol))
        if len(rows) > 32:
            out = [r"\begingroup", size, rf"\begin{{longtable}}{{@{{}}{spec}@{{}}}}"]
            if cap:
                if self.supp:
                    out[0] += rf"\renewcommand{{\thetable}}{{{cap[0]}}}"
                    out.append(rf"\caption{{{cap[1]}}}\\")
                else:
                    out.append(rf"\caption{{{cap[1]}}}\label{{tab:{cap[0]}}}\\")
            out += [r"\toprule", head, r"\midrule", r"\endfirsthead",
                    rf"\multicolumn{{{ncol}}}{{@{{}}l}}{{\textit{{Table {cap[0] if cap else ''} (continued)}}}}\\",
                    r"\toprule", head, r"\midrule", r"\endhead", r"\bottomrule", r"\endlastfoot", body,
                    r"\end{longtable}", r"\endgroup"]
            return "\n".join(out)
        lines = [r"\begin{table}[!htbp]", r"\centering", size]
        if cap:
            lines.append(self.caption("tab", *cap))
        if use_x:
            lines += [rf"\begin{{tabularx}}{{\textwidth}}{{@{{}}{spec}@{{}}}}", r"\toprule", head, r"\midrule",
                      body, r"\bottomrule", r"\end{tabularx}"]
        else:
            lines += [r"\begin{adjustbox}{max width=\textwidth}",
                      rf"\begin{{tabular}}{{@{{}}{spec}@{{}}}}", r"\toprule", head, r"\midrule",
                      body, r"\bottomrule", r"\end{tabular}", r"\end{adjustbox}"]
        lines.append(r"\end{table}")
        return "\n".join(lines)

    def figure_tex(self, path, num, cap):
        return "\n".join([r"\begin{figure}[!htbp]", r"\centering",
                          rf"\includegraphics[width={'0.62' if path in SINGLE_COL else ''}\textwidth]{{{FIGDIR}{path}.pdf}}",
                          self.caption("fig", num, cap), r"\end{figure}"])


def refs_to_labels(tex):
    """Main text: Table N / Fig. N -> \\ref so numbering follows first appearance."""
    def tabs(m):
        nums = re.findall(r"\d+", m.group(2))
        seps = re.findall(r"(, | and |–)", m.group(2))
        out = rf"\ref{{tab:{nums[0]}}}"
        for s, n in zip(seps, nums[1:]):
            out += {"–": "--"}.get(s, s) + rf"\ref{{tab:{n}}}"
        return m.group(1) + "~" + out
    tex = re.sub(r"(?<![A-Za-z])(Tables?) ((?:\d+)(?:(?:, | and |–)\d+)*)(?![\d.]*[A-Za-z])", tabs, tex)

    def figs(m):
        nums = re.findall(r"\d+", m.group(2))
        seps = re.findall(r"(, | and |–)", m.group(2))
        out = rf"\ref{{fig:{nums[0]}}}"
        for s, n in zip(seps, nums[1:]):
            out += {"–": "--"}.get(s, s) + rf"\ref{{fig:{n}}}"
        return m.group(1) + "~" + out
    return re.sub(r"(?<![A-Za-z])(Figs?\.) ((?:\d+)(?:(?:, | and |–)\d+)*)", figs, tex)


PREAMBLE = r"""\documentclass[preprint,12pt,authoryear]{elsarticle}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs,tabularx,array,adjustbox,longtable}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{float}
\usepackage{fvextra}
%LINENO%
\DeclareUnicodeCharacter{2212}{\ensuremath{-}}
\DeclareUnicodeCharacter{2265}{\ensuremath{\geq}}
\DeclareUnicodeCharacter{2264}{\ensuremath{\leq}}
\DeclareUnicodeCharacter{00D7}{\ensuremath{\times}}
\DeclareUnicodeCharacter{2192}{\ensuremath{\rightarrow}}
\DeclareUnicodeCharacter{2190}{\ensuremath{\leftarrow}}
\DeclareUnicodeCharacter{00B1}{\ensuremath{\pm}}
\DeclareUnicodeCharacter{00B0}{\ensuremath{^\circ}}
\DeclareUnicodeCharacter{03B2}{\ensuremath{\beta}}
\DeclareUnicodeCharacter{03BB}{\ensuremath{\lambda}}
\DeclareUnicodeCharacter{2032}{\ensuremath{'}}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\newcommand{\pandocbounded}[1]{#1}
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.15}
\biboptions{sort,semicolon}
\journal{Computers and Electronics in Agriculture}
% first page: page number only in the footer, so the corresponding-author note has room
\makeatletter
\def\ps@pprintTitle{\let\@oddhead\@empty\let\@evenhead\@empty
  \def\@oddfoot{\reset@font\hfil\thepage\hfil}\let\@evenfoot\@oddfoot}
\makeatother
"""


MARK = {"en": dict(abstract="## Abstract", kw=r"\*\*Keywords:\*\*", hl="### Highlights", nomen="### Nomenclature",
                  intro="## 1. Introduction", data="## Data availability"),
        "zh": dict(abstract="## 摘要", kw=r"\*\*关键词[：:]\*\*", hl="### 研究亮点", nomen="### 符号与缩写",
                   intro="## 1. 引言", data="## 数据可用性")}


def split_main(md, lang="en"):
    k = MARK[lang]
    title = re.search(r"^# (.+)$", md, re.M).group(1)
    abstract = re.search(rf"{k['abstract']}\n\n(.+?)\n\n{k['kw']}", md, re.S).group(1).strip()
    kw = [x.strip() for x in re.split(r"[;；] ?", re.search(rf"{k['kw']} ?(.+)", md).group(1))]
    hl = re.findall(r"^- (.+)$", re.search(rf"{k['hl']}\n\n(.+?)\n\n", md, re.S).group(1), re.M)
    nomen = re.search(rf"{k['nomen']}\n\n(.+?)\n---\n", md, re.S).group(1)
    body = md[md.index(k["intro"]):md.index(k["data"])]
    data = re.search(rf"{k['data']}\n\n(.+?)\n\n", md, re.S).group(1)
    return title, abstract, kw, hl, nomen, body, data


def headings(md, supp):
    """Remove manual section numbers (LaTeX numbers sections); demote one level."""
    def h(m):
        level, text = len(m.group(1)), m.group(2)
        if supp:
            mm = re.match(r"^(Appendix [A-Z]\.|[A-Z]\.\d+a?) (.*)$", text)
            text = mm.group(0) if mm else text
            return "#" * (level - 1) + " " + text + " {-}"
        text = re.sub(r"^\d+(\.\d+)*\.? ", "", text)
        return "#" * (level - 1) + " " + text
    return re.sub(r"^(#{2,6}) (.+)$", h, md, flags=re.M)


def tidy(tex):
    tex = re.sub(r"\\begin\{verbatim\}(.*?)\\end\{verbatim\}",
                 lambda m: "\\begin{Verbatim}[fontsize=\\tiny,breaklines]" + m.group(1) + "\\end{Verbatim}", tex, flags=re.S)
    tex = tex.replace(r"\begin{center}\rule{0.5\linewidth}{0.5pt}\end{center}", "")
    return re.sub(r"\n{3,}", "\n\n", tex)


def build_main(lang="en"):
    md = (PAPER / ("manuscript.md" if lang == "en" else "manuscript_zh.md")).read_text()
    if lang == "zh":
        md = zh_normalise(md)
    title, abstract, kw, hl, nomen, body, data = split_main(md, lang)
    d = Doc(headings(body, False), supp=False)
    body_tex = refs_to_labels(d.render())
    if lang == "zh":
        body_tex = re.sub(r"(?<![A-Za-z])Tables?~", "表~", body_tex)
        body_tex = re.sub(r"(?<![A-Za-z])Figs?\.~", "图~", body_tex)
    ntab = Doc(nomen, supp=False)
    nomen_rows = next(p for k, p in ntab.blocks if k == "table")[0]
    cells = [unstash(x) for x in md_inline([cites(c) for r in nomen_rows[1:] for c in r])]
    ab, dat, *hls = [unstash(x) for x in md_inline([cites(abstract), cites(data)] + hl)]
    nom = refs_to_labels("\n".join(f"{cells[2 * i]} & {cells[2 * i + 1]} \\\\" for i in range(len(nomen_rows) - 1)))
    tex = PREAMBLE.replace("%LINENO%", r"\usepackage{lineno}" + "\n" + r"\linenumbers")
    tex += r"""
\begin{document}
\begin{frontmatter}
\title{%s}
\author[a]{[Author 1]\corref{cor1}}
\ead{[e-mail address]}
\author[b]{[Author 2]}
\author[a]{[Author 3]}
\cortext[cor1]{Corresponding author.}
\newpageafter{author}
\affiliation[a]{organization={[Department, Institution]}, city={[City]}, postcode={[Postcode]}, country={[Country]}}
\affiliation[b]{organization={[Department, Institution]}, city={[City]}, postcode={[Postcode]}, country={[Country]}}

\begin{abstract}
%s
\end{abstract}

\begin{keyword}
%s
\end{keyword}
\end{frontmatter}

\section*{Nomenclature}
{\footnotesize
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{0.24\textwidth}X@{}}
\toprule
\textbf{Symbol / acronym} & \textbf{Meaning} \\
\midrule
%s
\bottomrule
\end{tabularx}}

%s

\section*{Data availability}
%s

\section*{CRediT authorship contribution statement}
[To be completed by the authors.]

\section*{Declaration of competing interest}
The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

\section*{Declaration of generative AI and AI-assisted technologies in the writing process}
[To be completed by the authors according to the journal's policy.]

\section*{Acknowledgements}
[Funding sources.]

\section*{Supplementary material}
Supplementary material (proofs, theory details, experimental details and full tables) is provided in a separate file.

\bibliographystyle{elsarticle-harv}
\bibliography{refs}
\end{document}
""" % (title, ab, " \\sep ".join(kw), nom, tidy(body_tex), dat)
    if lang == "zh":
        (OUT / "manuscript_zh.tex").write_text(to_zh(tex))
        return
    (OUT / "manuscript.tex").write_text(tex)
    # highlights are uploaded as a separate file (Elsevier: 3-5 bullets, at most 85 characters each)
    assert all(len(re.sub(r"\\[a-z]+|[{}$]", "", h)) <= 85 for h in hls), hls
    (OUT / "highlights.tex").write_text(r"""\documentclass[12pt]{article}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[margin=25mm]{geometry}
\pagestyle{empty}
\begin{document}
\section*{Highlights}
\begin{itemize}
%s
\end{itemize}
\end{document}
""" % "\n".join(rf"\item {h}" for h in hls))


def build_supp():
    md = (PAPER / "supplementary.md").read_text()
    title = re.search(r"^\*\*(.+?)\*\*$", md, re.M).group(1)
    body = md[md.index("**Names used"):]
    d = Doc(headings(body, True), supp=True)
    body_tex = tidy(d.render())
    tex = PREAMBLE.replace("%LINENO%", "") + r"""
\usepackage{etoolbox}
\begin{document}
\begin{center}
{\Large\bfseries Supplementary Material\par}\vspace{0.6em}
{\large %s\par}
\end{center}
\tableofcontents
\bigskip
%s
\clearpage
\bibliographystyle{elsarticle-harv}
\bibliography{refs}
\end{document}
""" % (title, body_tex)
    (OUT / "supplementary.tex").write_text(tex)


ZH_PRE = r"""\usepackage[UTF8,fontset=none,heading=false,scheme=chinese]{ctex}
\setCJKmainfont[BoldFont=Noto Serif CJK SC Bold]{Noto Serif CJK SC}
\setCJKsansfont{Noto Sans CJK SC}
\setCJKmonofont{Noto Sans Mono CJK SC}
\abstracttitle{摘要}
\keywordtitle{关键词}
\renewcommand{\figurename}{图}
\renewcommand{\tablename}{表}
\renewcommand{\refname}{参考文献}
"""


def zh_normalise(md):
    """Chinese captions and cross-references (表 3、图 2) -> the forms the parser and refs_to_labels expect."""
    for i, ch in enumerate("①②③④⑤⑥⑦⑧⑨"):
        md = md.replace(ch, f"（{i + 1}）")
    md = re.sub(r"^\*表 (S?\d+[a-z]?)[\u3000 ]+(.*)\*\s*$", r"*Table \1. \2*", md, flags=re.M)
    md = re.sub(r"^\*\*图 (S?\d+)\*\*[\u3000 ]*(.*)$", r"**Fig. \1.** \2", md, flags=re.M)
    # full-width parentheses around a citation -> ASCII, so that cites() turns them into \citep
    md = re.sub(r"（([^（）]*?[A-Z][\w'ïöé-]+(?: et al\.)?, (?:(?:19|20)\d\d|n\.d\.))）", r"(\1)", md)
    md = re.sub(r"(?<![A-Za-z0-9_*])表 ?(\d+)(?![\d.])", r"Table \1", md)
    md = re.sub(r"(?<![A-Za-z0-9_*地])图 ?(\d+)(?![\d.])", r"Fig. \1", md)
    return md


def to_zh(tex):
    """English template -> Chinese (xelatex + ctex); body text is already Chinese."""
    tex = tex.replace("\\usepackage[T1]{fontenc}\n\\usepackage[utf8]{inputenc}\n", "")
    tex = re.sub(r"\\DeclareUnicodeCharacter\{[0-9A-F]+\}\{.*\}\n", "", tex)
    tex = tex.replace("\\usepackage{lmodern}\n", "\\usepackage{lmodern}\n" + ZH_PRE)
    tex = re.sub(r"\\begin\{keyword\}.*?\\end\{keyword\}", lambda m: m.group(0).replace(" \\sep ", "；"), tex, flags=re.S)
    tex = re.sub(r"(?<![A-Za-z])Tables?~", "表~", tex)
    tex = re.sub(r"(?<![A-Za-z])Figs?\.~", "图~", tex)
    i = tex.index("\\begin{document}")
    tex = tex[:i] + tex[i:].replace("≥", "$\\geq$").replace("≤", "$\\leq$")
    tex = re.sub(r"（Table (\d+)）", r"（表~\\ref{tab:\1}）", tex)
    tex = tex.replace("\\begin{document}", "\\makeatletter\\patchcmd{\\printFirstPageNotes}{Email address:}{电子邮箱：}{}{}\\makeatother\n\\begin{document}", 1)
    for a, b in [("\\section*{Nomenclature}", "\\section*{符号与缩写}"),
                 ("\\textbf{Symbol / acronym} & \\textbf{Meaning}", "\\textbf{符号 / 缩写} & \\textbf{含义}"),
                 ("\\section*{Data availability}", "\\section*{数据可用性}"),
                 ("\\section*{CRediT authorship contribution statement}\n[To be completed by the authors.]",
                  "\\section*{作者贡献声明（CRediT）}\n［待作者填写。］"),
                 ("\\section*{Declaration of competing interest}\nThe authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.",
                  "\\section*{利益冲突声明}\n作者声明不存在可能影响本文工作的已知经济利益冲突或个人关系。"),
                 ("\\section*{Declaration of generative AI and AI-assisted technologies in the writing process}\n[To be completed by the authors according to the journal's policy.]",
                  "\\section*{写作过程中使用生成式人工智能及相关技术的声明}\n［待作者按期刊要求填写。］"),
                 ("\\section*{Acknowledgements}\n[Funding sources.]", "\\section*{致谢}\n［资助来源。］"),
                 ("\\section*{Supplementary material}\nSupplementary material (proofs, theory details, experimental details and full tables) is provided in a separate file.",
                  "\\section*{补充材料}\n证明、理论细节、实验细节与完整表格见补充材料（英文）。"),
                 ("\\cortext[cor1]{Corresponding author.}", "\\cortext[cor1]{通讯作者。}"),
                 ("\\ead{[e-mail address]}", "\\ead{［电子邮箱］}"),
                 ("[Author 1]", "［作者 1］"), ("[Author 2]", "［作者 2］"), ("[Author 3]", "［作者 3］")]:
        assert a in tex, a
        tex = tex.replace(a, b)
    return tex


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    if (PAPER / "manuscript_zh.md").exists():
        build_main("zh")
        used_keys.clear()
    build_main()
    main_keys = set(used_keys)
    build_supp()
    bib = (OUT / "refs.bib").read_text()
    allk = set(re.findall(r"@\w+\{([^,]+),", bib))
    print("main cites", len(main_keys), "of", len(allk), "; uncited in main:", sorted(allk - main_keys))
