from resume_from_linkedin.parser import split_sections, parse_skills

def test_split_sections_basic():
    text = "John Doe\nSenior DevOps Engineer\n\nExperience\nFoo — Bar\n\nSkills\nPython, AWS | Terraform"
    secs = split_sections(text)
    assert "Header" in secs and "Experience" in secs and "Skills" in secs

def test_parse_skills():
    block = "Python, AWS | Terraform • Docker"
    skills = parse_skills(block)
    assert "Python" in skills and "AWS" in skills and "Terraform" in skills and "Docker" in skills

