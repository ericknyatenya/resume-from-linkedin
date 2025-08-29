from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import pdfplumber

SECTION_HEADERS = [
    "About", "Summary", "Experience", "Education",
    "Licenses & Certifications", "Certifications",
    "Skills", "Projects", "Volunteer", "Organizations",
]

@dataclass
class Basics:
    name: str = ""
    title: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    summary: str = ""

@dataclass
class Job:
    title: str
    company: str
    start: str
    end: Optional[str]
    location: str = ""
    bullets: List[str] = field(default_factory=list)

@dataclass
class Edu:
    school: str
    degree: str
    start: str = ""
    end: str = ""

@dataclass
class ResumeData:
    basics: Basics = Basics()
    experience: List[Job] = field(default_factory=list)
    education: List[Edu] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    certs: List[str] = field(default_factory=list)

def _clean_text(t: str) -> str:
    # Join hyphenated line breaks and squeeze whitespace
    t = re.sub(r"-\n", "", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

def extract_text_from_pdf(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return _clean_text("\n".join(pages))

def split_sections(text: str) -> Dict[str, str]:
    # Build a regex to split by known LinkedIn-like headers
    header_re = r"|".join([re.escape(h) for h in SECTION_HEADERS])
    pattern = re.compile(rf"^({header_re})\s*$", re.MULTILINE)
    parts = pattern.split(text)
    # parts = [pre, H1, body1, H2, body2, ...]
    sections: Dict[str, str] = {}
    preface = parts[0].strip()
    if preface:
        sections["Header"] = preface
    for i in range(1, len(parts), 2):
        hdr = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections[hdr] = body
    return sections

def parse_basics(header_block: str) -> Basics:
    lines = [l for l in header_block.splitlines() if l.strip()]
    basics = Basics()
    if lines:
        basics.name = lines[0].strip()
    if len(lines) > 1:
        basics.title = lines[1].strip()
    # best-effort scraping for contact info
    all_text = " ".join(lines)
    email = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", all_text)
    phone = re.search(r"(\+\d{1,2}\s*)?(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})", all_text)
    linkedin = re.search(r"(https?://)?(www\.)?linkedin\.com/[^\s]+", all_text)
    location = re.search(r"(Located in|Location|Greater [\w\s]+|[A-Za-z\s]+, [A-Z]{2})", all_text)

    basics.email = email.group(0) if email else ""
    basics.phone = phone.group(0) if phone else ""
    basics.linkedin = linkedin.group(0) if linkedin else ""
    basics.location = location.group(0).replace("Location", "").replace("Located in", "").strip() if location else ""
    return basics

def parse_summary(block: str) -> str:
    return block.replace("\n", " ").strip()

def parse_experience(block: str) -> List[Job]:
    jobs: List[Job] = []
    # Heuristic: jobs separated by blank lines; first line "Title — Company"
    for chunk in re.split(r"\n\s*\n", block.strip()):
        lines = [l.strip("• ").strip() for l in chunk.splitlines() if l.strip()]
        if not lines:
            continue
        title_company = lines[0]
        m = re.match(r"^(.*?)\s+[–-]\s+(.*)$", title_company)
        title, company = (m.group(1), m.group(2)) if m else (title_company, "")
        dates_loc = lines[1] if len(lines) > 1 else ""
        m2 = re.search(r"(\w+\s+\d{4}|Present).*(\w+\s+\d{4}|Present)", dates_loc)
        start, end = "", ""
        if m2:
            # naive; you can refine with dateutil
            span = m2.group(0)
            span_parts = re.findall(r"(\w+\s+\d{4}|Present)", span)
            if span_parts:
                start = span_parts[0]
                end = span_parts[-1] if len(span_parts) > 1 else ""
        loc = ""
        loc_m = re.search(r"·\s*([A-Za-z.\s,-]+)$", dates_loc)
        if loc_m:
            loc = loc_m.group(1).strip()

        bullets = [l for l in lines[2:]]
        jobs.append(Job(title=title, company=company, start=start, end=end or None, location=loc, bullets=bullets))
    return jobs

def parse_education(block: str) -> List[Edu]:
    edus: List[Edu] = []
    for chunk in re.split(r"\n\s*\n", block.strip()):
        lines = [l.strip() for l in chunk.splitlines() if l.strip()]
        if not lines:
            continue
        school = lines[0]
        degree = lines[1] if len(lines) > 1 else ""
        dates = " ".join(lines[2:]) if len(lines) > 2 else ""
        ds = re.findall(r"\b(\d{4})\b", dates)
        start = ds[0] if ds else ""
        end = ds[1] if len(ds) > 1 else (ds[0] if ds else "")
        edus.append(Edu(school=school, degree=degree, start=start, end=end))
    return edus

def parse_skills(block: str) -> List[str]:
    text = block.replace("\n", " ")
    # LinkedIn PDFs often list skills comma- or pipe-separated
    parts = re.split(r"[|,•]", text)
    skills = [p.strip() for p in parts if p.strip()]
    # de-dup preserving order
    seen = set()
    uniq = []
    for s in skills:
        k = s.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(s)
    return uniq

def parse_certs(block: str) -> List[str]:
    lines = [l.strip("• ").strip() for l in block.splitlines() if l.strip()]
    return lines

def parse_resume(text: str) -> ResumeData:
    sections = split_sections(text)
    data = ResumeData()

    if "Header" in sections:
        data.basics = parse_basics(sections["Header"])
    # summary might be under About or Summary
    for key in ("About", "Summary"):
        if key in sections and sections[key].strip():
            data.basics.summary = parse_summary(sections[key]); break
    if "Experience" in sections:
        data.experience = parse_experience(sections["Experience"])
    if "Education" in sections:
        data.education = parse_education(sections["Education"])
    for key in ("Skills",):
        if key in sections:
            data.skills = parse_skills(sections[key])
    for key in ("Licenses & Certifications", "Certifications"):
        if key in sections:
            data.certs = parse_certs(sections[key])
    return data

