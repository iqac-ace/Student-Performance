PROGRESS_RULES = {

    "ACADEMIC": {
        "name": "Academic Performance",
        "max_points": 20,

        "subtopics": {
            "PLUS2": {
                "label": "+2 / 12th Standard Performance",
                "points": 0,
                "requirements": [
                    "12th percentage",
                    "Board",
                    "School",
                    "Year of passing"
                ]
            },

            "CGPA_9": {
                "label": "CGPA ≥ 9.0",
                "points": 20,
                "requirements": ["CGPA / SGPA"]
            },

            "CGPA_8": {
                "label": "CGPA 8.0 - 8.99",
                "points": 17,
                "requirements": ["CGPA / SGPA"]
            },

            "CGPA_7": {
                "label": "CGPA 7.0 - 7.99",
                "points": 14,
                "requirements": ["CGPA / SGPA"]
            },

            "CGPA_6": {
                "label": "CGPA 6.0 - 6.99",
                "points": 10,
                "requirements": ["CGPA / SGPA"]
            },

            "CGPA_5": {
                "label": "CGPA 5.0 - 5.99",
                "points": 6,
                "requirements": ["CGPA / SGPA"]
            },

            "CGPA_LOW": {
                "label": "CGPA Below 5.0",
                "points": 3,
                "requirements": ["CGPA / SGPA"]
            }
        }
    },


    "ATTENDANCE": {
        "name": "Attendance & Academic Discipline",
        "max_points": 10,

        "subtopics": {
            "ATT_95": {
                "label": "Attendance ≥ 95%",
                "points": 10,
                "requirements": ["Attendance Percentage"]
            },

            "ATT_90": {
                "label": "Attendance 90 - 94%",
                "points": 8,
                "requirements": ["Attendance Percentage"]
            },

            "ATT_85": {
                "label": "Attendance 85 - 89%",
                "points": 6,
                "requirements": ["Attendance Percentage"]
            },

            "ATT_80": {
                "label": "Attendance 80 - 84%",
                "points": 4,
                "requirements": ["Attendance Percentage"]
            },

            "ATT_LOW": {
                "label": "Attendance Below 80%",
                "points": 0,
                "requirements": ["Attendance Percentage"]
            }
        }
    },


    "LEARNING": {
        "name": "Learning & Certification",
        "max_points": 10,

        "subtopics": {
            "CERT_3": {
                "label": "3 or More Recognized Certifications",
                "points": 10,
                "requirements": [
                    "Certificate Name",
                    "Provider / Institution",
                    "Completion Date"
                ]
            },

            "CERT_2": {
                "label": "2 Certifications",
                "points": 8,
                "requirements": [
                    "Certificate Name",
                    "Provider / Institution"
                ]
            },

            "CERT_1": {
                "label": "1 Certification",
                "points": 6,
                "requirements": [
                    "Certificate Name",
                    "Provider / Institution"
                ]
            },

            "MOOC": {
                "label": "NPTEL / SWAYAM / MOOC / ODL Completed",
                "points": 4,
                "requirements": [
                    "Course Name",
                    "Platform",
                    "Completion Details"
                ]
            },

            "LEARNING_PARTICIPATION": {
                "label": "Structured Learning Programme Participation",
                "points": 2,
                "requirements": [
                    "Programme Name",
                    "Organising Institution"
                ]
            }
        }
    },


    "TECHNICAL": {
        "name": "Technical Skills & Projects",
        "max_points": 15,

        "subtopics": {
            "TECH_NATIONAL": {
                "label": "National / International Technical Achievement",
                "points": 15,
                "requirements": [
                    "Competition / Project Name",
                    "Level",
                    "Achievement"
                ]
            },

            "HACK_WIN": {
                "label": "Major Hackathon / Technical Competition Achievement",
                "points": 12,
                "requirements": [
                    "Event Name",
                    "Organiser",
                    "Achievement"
                ]
            },

            "FUNCTIONAL_PROJECT": {
                "label": "Functional Industry / Technical Project",
                "points": 10,
                "requirements": [
                    "Project Title",
                    "Technology Used",
                    "Project Description"
                ]
            },

            "ENGINEERING_EXPLORATION": {
                "label": "Engineering Exploration / Substantial Project",
                "points": 8,
                "requirements": [
                    "Project Title",
                    "Project Description"
                ]
            },

            "HACK_PARTICIPATION": {
                "label": "Hackathon / Technical Competition Participation",
                "points": 5,
                "requirements": [
                    "Event Name",
                    "Organiser"
                ]
            },

            "BASIC_PROJECT": {
                "label": "Basic Technical Project / Activity",
                "points": 3,
                "requirements": [
                    "Activity / Project Name"
                ]
            }
        }
    },


    "INTERNSHIP": {
        "name": "Internship & Industry Exposure",
        "max_points": 10,

        "subtopics": {
            "INTERNSHIP_PPO": {
                "label": "Internship + Excellent Evaluation / PPO",
                "points": 10,
                "requirements": [
                    "Company Name",
                    "Internship Title",
                    "Duration",
                    "Evaluation / PPO Details"
                ]
            },

            "INTERNSHIP_6": {
                "label": "Internship ≥ 6 Weeks",
                "points": 8,
                "requirements": [
                    "Company Name",
                    "Internship Title",
                    "Duration"
                ]
            },

            "INTERNSHIP_4": {
                "label": "Internship 4 - 5 Weeks",
                "points": 6,
                "requirements": [
                    "Company Name",
                    "Internship Title",
                    "Duration"
                ]
            },

            "SHORT_INTERNSHIP": {
                "label": "Short Internship / Industry Project",
                "points": 4,
                "requirements": [
                    "Organisation",
                    "Activity / Project Name"
                ]
            },

            "INDUSTRIAL_VISIT": {
                "label": "Industrial Visit / Expert Interaction",
                "points": 2,
                "requirements": [
                    "Company / Expert Name",
                    "Visit / Programme Date"
                ]
            }
        }
    },


    "RESEARCH": {
        "name": "Research, Innovation & IPR",
        "max_points": 10,

        "subtopics": {
            "PATENT_GRANTED": {
                "label": "Granted Patent / Major Research Achievement",
                "points": 10,
                "requirements": [
                    "Patent / Research Title",
                    "Patent Number / Reference"
                ]
            },

            "PATENT_PUBLISHED": {
                "label": "Published Patent / Scopus / WoS Publication",
                "points": 9,
                "requirements": [
                    "Title",
                    "Journal / Patent Details",
                    "DOI / Reference"
                ]
            },

            "PUBLICATION": {
                "label": "Research Publication / Significant Research Project",
                "points": 7,
                "requirements": [
                    "Research Title",
                    "Publication / Project Details"
                ]
            },

            "PAPER_PRESENTATION": {
                "label": "Paper Presentation / IIC Innovation Project",
                "points": 5,
                "requirements": [
                    "Title",
                    "Event / Institution"
                ]
            },

            "RESEARCH_PARTICIPATION": {
                "label": "Prototype / Research / Idea Submission",
                "points": 3,
                "requirements": [
                    "Title",
                    "Description"
                ]
            },

            "RESEARCH_AWARENESS": {
                "label": "Research Awareness Programme",
                "points": 1,
                "requirements": [
                    "Programme Name"
                ]
            }
        }
    },


    "CAREER": {
        "name": "Placement & Career Readiness",
        "max_points": 10,

        "subtopics": {
            "PLACEMENT": {
                "label": "Placement / PPO / Higher Study Admission",
                "points": 10,
                "requirements": [
                    "Company / Institution",
                    "Offer / Admission Details"
                ]
            },

            "ADVANCED_READINESS": {
                "label": "Advanced Placement Readiness",
                "points": 8,
                "requirements": [
                    "Programme / Assessment Name"
                ]
            },

            "ASSESSMENT": {
                "label": "Strong Aptitude / Coding / Interview Performance",
                "points": 6,
                "requirements": [
                    "Assessment Name",
                    "Score / Result"
                ]
            },

            "PLACEMENT_TRAINING": {
                "label": "Completed Placement Training",
                "points": 4,
                "requirements": [
                    "Training Name",
                    "Training Provider"
                ]
            },

            "CAREER_PROGRAMME": {
                "label": "Career Development Programme Participation",
                "points": 2,
                "requirements": [
                    "Programme Name"
                ]
            }
        }
    },


    "LEADERSHIP": {
        "name": "Leadership & Student Engagement",
        "max_points": 5,

        "subtopics": {
            "MAJOR_LEADER": {
                "label": "Student Leader / Club Office Bearer",
                "points": 5,
                "requirements": [
                    "Role",
                    "Club / Organisation",
                    "Period"
                ]
            },

            "CLUB_LEADER": {
                "label": "Domain Club / Professional Society Leader",
                "points": 4,
                "requirements": [
                    "Role",
                    "Club / Society"
                ]
            },

            "ACTIVE_MEMBER": {
                "label": "Regular Club / Professional Society Participation",
                "points": 3,
                "requirements": [
                    "Club / Society",
                    "Activities"
                ]
            },

            "MENTORING": {
                "label": "Peer Teaching / Mentoring / Activity Participation",
                "points": 2,
                "requirements": [
                    "Activity",
                    "Role"
                ]
            },

            "MEMBER": {
                "label": "Membership Only",
                "points": 1,
                "requirements": [
                    "Club / Society Name"
                ]
            }
        }
    },


    "SOCIAL": {
        "name": "Social Responsibility & Institutional Contribution",
        "max_points": 5,

        "subtopics": {
            "SOCIAL_LEAD": {
                "label": "Led Major NSS / UBA / SDG / IQAC Initiative",
                "points": 5,
                "requirements": [
                    "Programme Name",
                    "Role",
                    "Date"
                ]
            },

            "SOCIAL_3PLUS": {
                "label": "Active Participation in 3 or More Activities",
                "points": 4,
                "requirements": [
                    "Activity Details"
                ]
            },

            "SOCIAL_2": {
                "label": "Participation in 2 Activities",
                "points": 3,
                "requirements": [
                    "Activity Details"
                ]
            },

            "SOCIAL_1": {
                "label": "Participation in 1 Activity",
                "points": 2,
                "requirements": [
                    "Activity Name"
                ]
            },

            "SOCIAL_AWARENESS": {
                "label": "Awareness Programme",
                "points": 1,
                "requirements": [
                    "Programme Name"
                ]
            }
        }
    },


    "SPORTS": {
        "name": "Sports, Cultural & Achievements",
        "max_points": 5,

        "subtopics": {
            "NATIONAL": {
                "label": "National / International Achievement",
                "points": 5,
                "requirements": [
                    "Event Name",
                    "Achievement",
                    "Level"
                ]
            },

            "STATE": {
                "label": "State / University / Inter-Zone Achievement",
                "points": 4,
                "requirements": [
                    "Event Name",
                    "Achievement"
                ]
            },

            "DISTRICT": {
                "label": "District / Regional Achievement",
                "points": 3,
                "requirements": [
                    "Event Name",
                    "Achievement"
                ]
            },

            "INSTITUTION": {
                "label": "Institution Level Achievement",
                "points": 2,
                "requirements": [
                    "Event Name"
                ]
            },

            "PARTICIPATION": {
                "label": "Participation",
                "points": 1,
                "requirements": [
                    "Event Name"
                ]
            }
        }
    }
}