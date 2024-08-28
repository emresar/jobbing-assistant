system_prompt = """
You are an AI assistant that helps with job applications. You are given comnpany infos and job postings and a candidate's CV. You need to evaluate the CV and provide suggestions for improvement.  Here is my CV:
"""


job_rating_prompt = """
Please follow these steps:

1. Carefully read and understand the job posting and company information.
2. Thoroughly review the provided CV. Keep in mind that more recent experiences are more relevant than older ones.
3. If provided, consider any additional context about the applicant that might be relevant to the position.

4. Highlight the top 3-5 qualifications from the CV that best match the job requirements. 

5. Identify any gaps or areas for improvement in the CV relative to the job requirements.

6. Suggest 2-3 specific ways the candidate could improve their CV or skillset to better match the job requirements.

7. Based on the available information, briefly assess how well the candidate might fit into the company culture.

8. Evaluate the CV's fit for the position based on the following criteria where each rating should reflect the candidate's relevant  qualifications carefully assesing the candidate's missing qualifications and areas of improvement:
   a) Relevant technical skills (rate 1-10)
   b) Relevant workexperience (rate 1-10)
   c) Education and certifications (rate 1-10)
   d) Soft skills and cultural fit (rate 1-10)

9. Provide an overall fit score (1-10) based on the above criteria.

Please structure your response as follows:

Top Matching Qualifications:
1. [Qualification 1]
2. [Qualification 2]
3. [Qualification 3]

Areas for Improvement:
1. [Area 1]
2. [Area 2]

Suggestions for Improvement:
1. [Suggestion 1]
2. [Suggestion 2]

Cultural Fit Assessment:
[Brief assessment of cultural fit]

Evaluation Scores:
- Relevant technical skills: [score]/10
- Relevant work experience: [score]/10
- Education and certifications: [score]/10
- Soft skills and cultural fit: [score]/10
- Overall fit score: [score]/10

Additional Comments:
[Any other relevant observations or recommendations]
"""


cover_letter_prompt = """
Please follow these steps:

1. Carefully read and understand the job posting, company information, and my CV.
2. If provided, consider any additional context about the applicant that might be relevant to the position.
3. Create a compelling cover letter that highlights my qualifications and experience relevant to the job requirements.
4. Incorporate any relevant information from the additional context to personalize the letter and demonstrate my unique fit for the role.
5. Keep the letter concise, professional, and engaging, typically between 300-450 words.

Structure the cover letter as follows:

1. Opening paragraph: Introduce the candidate and state the position they're applying for.
2. Body paragraphs (1-2): Highlight relevant skills, experiences, and achievements that make the candidate a strong fit for the role. Also mention if the candidate lacks any qualifications or experiences that are relevant to the position, and suggest ways to improve them based on my know-how and experience.
3. Closing paragraph: Express enthusiasm for the opportunity and invite further discussion.

Please write the cover letter in a professional tone, addressing it to the hiring manager or relevant contact if provided in the job posting. If no specific contact is given, use a general salutation such as "Dear Hiring Manager,". 

Use first person point of view and avoid using the term "I" or "me".

Incorporate any additional context provided to make the letter more personalized and relevant.
"""

cv_edit_suggestions_prompt = """
As an AI assistant specializing in resume optimization, your task is to suggest edits for a CV to better match a specific job posting for a Senior Machine Learning Engineer position. Please follow these steps:

1. Carefully read and understand the job posting, company information, and the candidate's current CV.
2. If provided, consider any additional context about the applicant that might be relevant to the position.
3. Analyze the CV and identify areas that could be improved to better align with the job requirements and company culture.
4. Provide specific, actionable suggestions for editing the CV, focusing on:
   a) Content: Adding relevant experiences, skills, or achievements
   b) Structure: Reorganizing sections or information for better impact
   c) Language: Improving phrasing or using keywords from the job posting
   d) Formatting: Enhancing readability and visual appeal

5. Prioritize suggestions that will have the most significant impact on the CV's effectiveness for this specific job application.

Please provide the edited CV in the same structure as in the original markdown file, incorporating the suggested edits.
"""


"""

Please structure your response as follows:

Content Suggestions:
1. [Suggestion 1]
2. [Suggestion 2]
3. [Suggestion 3]

Structure Suggestions:
1. [Suggestion 1]
2. [Suggestion 2]

Language Suggestions:
1. [Suggestion 1]
2. [Suggestion 2]

Formatting Suggestions:
1. [Suggestion 1]
2. [Suggestion 2]

Key Skills to Highlight:
1. [Skill 1]
2. [Skill 2]
3. [Skill 3]

Additional Recommendations:
[Any other relevant suggestions or observations]

Please provide clear, specific examples or rewrites where appropriate to illustrate your suggestions.
"""


additional_context_for_website = """ Currently the company {company_name} wants to build a new AI team to tackle new problems although there is no official job posting. First, outline the key business areas of the company {company_name}. Please summarize them under topics and elaborate on each in your final response.
"""
