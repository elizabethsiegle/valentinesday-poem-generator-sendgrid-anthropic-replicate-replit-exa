from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from exa_py import Exa
import os
from PIL import Image
import re
import replicate
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
     Mail)
import streamlit as st

with open('./style/style.css') as f:
    css = f.read()
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

EXA_API_KEY = os.environ['EXA_API_KEY']
SENDGRID_API_KEY = os.environ['SENDGRID_API_KEY']
ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']
anthropic = Anthropic(
    api_key=ANTHROPIC_API_KEY
)


def main():
    st.title("Poems for your Boo👻 ❤️ 💌") 
    st.write("Built w/ Anthropic, SendGrid, Streamlit, Exa, && Replicate") 
    image = Image.open('ghostheart.png')
    st.image(image)

    receiver_name = st.text_input("Poem receiver name")
    jasonmomoaslider = st.select_slider(
    'How much do you like them on a scale from just a friend to Jason Momoa', options=['just a friend', 'coffee shop crush', 'hot for a coworker', 'top of the roster', 'the love of your life', 'Jason Momoa'])
    st.write("You like this person ", jasonmomoaslider, 'on a scale of 0 to Jason Momoa')
    receiver_description = st.text_area(
      "What is the vibe ✨ of this person",
      "Cheugy Millennial Woman who loves Taylor Swift and saying 'Slay' but it never sounds right. "
    )
    model_toggle = st.radio("What LLM would you like to use", # lol it rhymes
      [":rainbow[llama-2-70b-chat]", "***Claude***"],
      captions = ["Hosted on Replicate", "Thank you, Anthropic"]
    ) 
    addons = st.multiselect(
        'What would you like your poem to include?',
        ['Star Wars quote', 'Shrek quote', 'Taylor Swift lyrics', 'Klay Thompson quote'],
        ['Star Wars quote', 'Shrek quote']
    )

    st.write('You selected:', addons)

    astrology_sign = st.selectbox(
        'What is their astrology sign? ♓️♈️',
        ['Virgo', 'Gemini', 'Leo', 'Libra', 'Sagittarius', 'Taurus', 'Aquarius', 'Aries', 'Capricorn', 'Cancer', 'Scorpio', 'Pisces']
    )
    st.write('You selected:', astrology_sign)

    user_email = st.text_input("Email to send love poem and gift recs to📧", "lol@gmail.com")
    poem = ''
    if st.button('Generate a poem and gift ideas w/ AI 🧠🤖') and astrology_sign and addons and model_toggle and receiver_name and receiver_description and user_email:
        with st.spinner('Processing📈...'):
            exa = Exa(EXA_API_KEY)
            exa_resp = exa.search(
                f"thoughtful, fun gift for someone who's a {astrology_sign} and is described as {receiver_description}",
                num_results=3,
                start_crawl_date="2024-01-01",
                end_crawl_date="2024-02-14",
            )
            print(exa_resp)

            # regex pattern to extract title, URL, and score
            pattern = r"Title: (.+)\nURL: (.+)\nID: .*\nScore: ([\d.]+)"

            # Find all matches w/ the regex pattern
            matches = re.findall(pattern, str(exa_resp))

            # Iterate over the matches and add the extracted information to an array of gifts
            gifts = []
            for match in matches:
                title, url, score = match
                gifts.append(f'{title.strip()}: {url.strip()}')
            COPY_PROMPT = f"""
              You are a copy editor. Edit the following blurb and                return only that edited blurb, ensuring the only 
              pronouns used are "I": {receiver_description}. 
              There should be no preamble.
            """
            if model_toggle == "***Claude***":
                completion1 = anthropic.completions.create(
                    model="claude-instant-1.2", # claude-2.1
                    max_tokens_to_sample=700,
                    prompt=f"{HUMAN_PROMPT}: {COPY_PROMPT}. {AI_PROMPT}",
                )
                print(completion1.completion)
                newPronouns = completion1.completion

                MAIN_PROMPT= f"""
Please make me laugh by writing a short, silly, lighthearted, complimentary, lovey-dovey poem that rhymes about the following person named {receiver_name}. I like this person {jasonmomoaslider} on a scale of 0 to 100--the closer to 100, the saucier the poem should be. The closer to 0, the more platonic the poem should be.
<receiver_description>{newPronouns}</receiver_description>. 
I would enjoy it if the poem also jokingly included the common characteristics of a person that has the astrological sign of {astrology_sign} and include {addons}. 
Return only the poem where each new line ends with a new line character.
"""

                completion = anthropic.completions.create(
                    model="claude-2.1",
                    max_tokens_to_sample=1000,
                    prompt=f"{HUMAN_PROMPT}: {MAIN_PROMPT}. {AI_PROMPT}",
                )
                newpoem = completion.completion
                print(newpoem)
                st.markdown(f'Generated poem:  {newpoem}')


            elif model_toggle == ":rainbow[llama-2-70b-chat]":
                editpronouns = replicate.run(
                    "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",r
                    input={
                        "prompt": COPY_PROMPT,
                        "max_new_tokens": 700
                    }
                )
                newpronounsblurb = ''
                for item in editpronouns:
                    newpronounsblurb+=item 
                    print(item, end="")
                print("newpronounsblurb ", newpronounsblurb)

                MAIN_PROMPT= f"""
                With no preamble, please make me laugh by writing a short, silly, lighthearted, complimentary, lovey-dovey poem that rhymes about the following person named {receiver_name}. 
<receiver_description>{newpronounsblurb}</receiver_description>.
I like this person {jasonmomoaslider} on a scale of 0 to 100--the closer to 100, the saucier the poem should be. The closer to 0, the more platonic the poem should be.
I would enjoy it if the poem also jokingly included the common characteristics of a person that has the astrological sign of {astrology_sign}
                and something about {addons}. 
                Return only the poem. 
"""

                poem = replicate.run(
                    "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",
                    input={
                        "prompt": MAIN_PROMPT,
                        "max_new_tokens": 1000
                    }
                )
                newpoem = ''
                for item in poem:
                    newpoem+=item
                    print(item, end="")
                print("newpoem ", newpoem)


                st.markdown(f'The generated poem: {newpoem}')

            output_pic = replicate.run(
                "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
                input={
                    "prompt": f"Please generate a G-rated cute image of a {astrology_sign} including hearts that I can show my toddler cousin and my grandma",
                    "width": 448,
                    "height": 448
                }
            )
            print(output_pic[0])
            message = Mail(
                from_email='love@poem.com',
                to_emails=user_email,
                subject='Personal poem for you!❤️',
                html_content=f'''
                <img src="{output_pic[0]}"</img>
                <p>{newpoem}</p>
                <p> ❤️😘🥰</p>
                '''
            )

            sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
            response = sg.send(message)
            print(response.status_code, response.body, response.headers)
            if response.status_code == 202:
                st.success("Email sent! Tell your ✨friend✨ to check their email for their poem and image")
                print(f"Response Code: {response.status_code} \n Email sent!")
            else:
                st.warning("Email not sent--check console")
    else:
        st.write("Check that you filled out each textbox and selected something for each question!")


    footer="""
    <footer>
        <p>Developed with ❤ in SF🌁</p> 
        <p>✅ out the code on <a href="https://github.com/elizabethsiegle/loveletter-generator-anthropic-sendgrid" target="_blank">GitHub</a></p>
    </footer>
    """
    st.markdown(footer,unsafe_allow_html=True)

if __name__ == "__main__":
    main() 