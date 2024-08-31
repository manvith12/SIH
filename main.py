import streamlit as st
import json
import httpx
from PIL import Image
from io import BytesIO
import time

# Define the HTTP client
client = httpx.Client(
    headers={
        "x-ig-app-id": "936619743392459",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "*/*",
    }
)

def get_data_with_pagination(url, limit=5):
    """Retrieve data with pagination"""
    data_list = []
    while len(data_list) < limit:
        result = client.get(url)
        data = json.loads(result.content)
        
        if not data.get('data', {}):
            break

        data_list.extend(data.get('data', []))
        
        # Check if we have reached the limit
        if len(data_list) >= limit:
            break
        
        # Update URL for the next page
        url = data.get('pagination', {}).get('next_url', None)
        if not url:
            break

    return data_list[:limit]

@st.cache_data
def scrape_user(username: str):
    """Scrape Instagram user's data and extract relevant info, limited to the first 5 posts."""
    try:
        result = client.get(f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}")
        
        # Check if the request was successful
        if result.status_code != 200:
            return f"Failed to retrieve data. Status code: {result.status_code}", [], []

        # Attempt to parse the response content as JSON
        try:
            data = json.loads(result.content)
        except json.JSONDecodeError:
            return "Error decoding JSON response from the server.", [], []

        user_info = data.get("data", {}).get("user", {})
        if not user_info:
            return "User not found or unable to retrieve data.", [], []

        # Extract user data with NoneType handling
        user = {
            "Username": user_info.get("username", "N/A"),
            "Full Name": user_info.get("full_name", "N/A"),
            "ID": user_info.get("id", "N/A"),
            "Category": user_info.get("category_name", "N/A"),
            "Business Category": user_info.get("business_category_name", "N/A"),
            "Phone": user_info.get("business_phone_number", "N/A"),
            "Email": user_info.get("business_email", "N/A"),
            "Biography": user_info.get("biography", "N/A"),
            "Bio Links": [link.get("url") for link in user_info.get("bio_links", []) if link.get("url")],
            "Homepage": user_info.get("external_url", "N/A"),
            "Followers": f"{user_info.get('edge_followed_by', {}).get('count', 0):,}",
            "Following": f"{user_info.get('edge_follow', {}).get('count', 0):,}",
            "Facebook ID": user_info.get("fbid", "N/A"),
            "Is Private": user_info.get("is_private", "N/A"),
            "Is Verified": user_info.get("is_verified", "N/A"),
            "Profile Image": user_info.get("profile_pic_url_hd", "N/A"),
            "Video Count": user_info.get("edge_felix_video_timeline", {}).get("count", 0),
            "Image Count": user_info.get("edge_owner_to_timeline_media", {}).get("count", 0),
            "Saved Count": user_info.get("edge_saved_media", {}).get("count", 0),
            "Collections Count": user_info.get("edge_saved_media", {}).get("count", 0),
            "Related Profiles": [profile.get("node", {}).get("username", "N/A") for profile in user_info.get("edge_related_profiles", {}).get("edges", [])],
        }

        # Retrieve videos (limit to 5) with NoneType handling
        videos = user_info.get("edge_felix_video_timeline", {}).get("edges", [])[:5]
        video_info = []
        for video in videos:
            video_node = video.get("node", {})
            video_info.append({
                "ID": video_node.get("id", "N/A"),
                "Title": video_node.get("title", "N/A"),
                "Shortcode": video_node.get("shortcode", "N/A"),
                "Thumbnail": video_node.get("display_url", "N/A"),
                "URL": video_node.get("video_url", "N/A"),
                "Views": video_node.get("video_view_count", 0),
                "Tagged": [tag.get("node", {}).get("username", "N/A") for tag in video_node.get("edge_media_to_tagged_user", {}).get("edges", [])],
                "Captions": [caption.get("node", {}).get("text", "N/A") for caption in video_node.get("edge_media_to_caption", {}).get("edges", [])],
                "Comments Count": video_node.get("edge_media_to_comment", {}).get("count", 0),
                "Comments Disabled": video_node.get("comments_disabled", False),
                "Taken At": video_node.get("taken_at_timestamp", "N/A"),
                "Likes": video_node.get("edge_liked_by", {}).get("count", 0),
                "Location": video_node.get("location", {}).get("name", "N/A"),
                "Duration": video_node.get("video_duration", "N/A"),
            })

        # Retrieve images (limit to 5) with NoneType handling
        images = user_info.get("edge_owner_to_timeline_media", {}).get("edges", [])[:5]
        image_info = []
        for image in images:
            image_node = image.get("node", {})
            image_info.append({
                "ID": image_node.get("id", "N/A"),
                "Title": image_node.get("title", "N/A"),
                "Shortcode": image_node.get("shortcode", "N/A"),
                "Source": image_node.get("display_url", "N/A"),
                "Views": image_node.get("video_view_count", 0),
                "Tagged": [tag.get("node", {}).get("username", "N/A") for tag in image_node.get("edge_media_to_tagged_user", {}).get("edges", [])],
                "Captions": [caption.get("node", {}).get("text", "N/A") for caption in image_node.get("edge_media_to_caption", {}).get("edges", [])],
                "Comments Count": image_node.get("edge_media_to_comment", {}).get("count", 0),
                "Comments Disabled": image_node.get("comments_disabled", False),
                "Taken At": image_node.get("taken_at_timestamp", "N/A"),
                "Likes": image_node.get("edge_liked_by", {}).get("count", 0),
                "Location": image_node.get("location", {}).get("name", "N/A"),
                "Accessibility Caption": image_node.get("accessibility_caption", "N/A"),
                "Duration": image_node.get("video_duration", "N/A"),
            })

        return user, video_info, image_info
    except Exception as e:
        return f"An error occurred: {e}", [], []



def display_user_info(user_info):
    """Display the user's information"""
    st.subheader("User Information")
    if isinstance(user_info, str):
        st.error(user_info)
    else:
        # Styling the layout using containers, columns, and markdown
        with st.container():
            col1, col2 = st.columns([2, 3])
            with col1:
                st.write(f"**Username:** {user_info.get('Username')}")
                st.write(f"**Full Name:** {user_info.get('Full Name')}")
                st.write(f"**ID:** {user_info.get('ID')}")
                st.write(f"**Category:** {user_info.get('Category')}")
                st.write(f"**Business Category:** {user_info.get('Business Category')}")
                st.write(f"**Phone:** {user_info.get('Phone')}")
                st.write(f"**Email:** {user_info.get('Email')}")
                st.write(f"**Biography:** {user_info.get('Biography')}")
                st.write(f"**Bio Links:** {', '.join([f'[Link]({url})' for url in user_info.get('Bio Links', [])])}")
                st.write(f"**Homepage:** [Homepage Link]({user_info.get('Homepage')})")
                st.write(f"**Followers:** {user_info.get('Followers')}")
                st.write(f"**Following:** {user_info.get('Following')}")
                st.write(f"**Facebook ID:** {user_info.get('Facebook ID')}")
                st.write(f"**Private Account:** {'Yes' if user_info.get('Is Private') else 'No'}")
                st.write(f"**Verified Account:** {'Yes' if user_info.get('Is Verified') else 'No'}")
                st.write(f"**Video Count:** {user_info.get('Video Count')}")
                st.write(f"**Image Count:** {user_info.get('Image Count')}")
                st.write(f"**Saved Count:** {user_info.get('Saved Count')}")
                st.write(f"**Collections Count:** {user_info.get('Collections Count')}")
                st.write(f"**Related Profiles:** {', '.join(user_info.get('Related Profiles', []))}")

            with col2:
                # Display profile image
                if user_info.get('Profile Image'):
                    try:
                        response = client.get(user_info.get('Profile Image'))
                        img = Image.open(BytesIO(response.content))
                        st.image(img, caption="Profile Picture", use_column_width=True)
                    except Exception as e:
                        st.error(f"Error loading profile image: {e}")

def display_media(media_list, media_type):
    """Display user's media (videos or images)"""
    st.subheader(f"{media_type.capitalize()}s")
    
    if not media_list:
        st.write(f"No {media_type}s found.")
        return
    
    # Sort media (optional)
    sort_by = st.selectbox(f"Sort {media_type}s by:", ["Likes", "Comments", "Date"], key=media_type)
    
    if sort_by == "Likes":
        media_list = sorted(media_list, key=lambda x: x.get('Likes', 0), reverse=True)
    elif sort_by == "Comments":
        media_list = sorted(media_list, key=lambda x: x.get('Comments Count', 0), reverse=True)
    elif sort_by == "Date":
        media_list = sorted(media_list, key=lambda x: x.get('Taken At', 0), reverse=True)
    
    # Thumbnail size option
    thumbnail_size = st.radio("Thumbnail Size:", ["Small", "Large"], key=f"{media_type}_thumb")

    for media in media_list:
        with st.expander(f"{media_type.capitalize()} {media.get('ID')}"):
            st.write(f"**Title:** {media.get('Title')}")
            st.write(f"**Shortcode:** {media.get('Shortcode')}")
            st.write(f"**Likes:** {media.get('Likes')}")
            st.write(f"**Comments:** {media.get('Comments Count')}")
            st.write(f"**Location:** {media.get('Location')}")
            st.write(f"**Tagged Users:** {', '.join(media.get('Tagged', []))}")
            st.write(f"**Taken At:** {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(media.get('Taken At')))}")
            
            if media_type == "video" and media.get("URL"):
                st.video(media.get("URL"))
            else:
                if thumbnail_size == "Small":
                    st.image(media.get("Thumbnail"), width=150)
                else:
                    st.image(media.get("Thumbnail"), width=300)

            st.write(f"**Accessibility Caption:** {media.get('Accessibility Caption')}")
    
    # Allow data download
    json_data = json.dumps(media_list, indent=4)
    st.download_button("Download Media Data", json_data, file_name=f"{media_type}_data.json", mime="application/json")

# Main streamlit app function
def main():
    st.title("Instagram User Scraper")

    # Input for Instagram username
    username = st.text_input("Enter the Instagram username", placeholder="Username")
    
    # Action button to trigger scraping
    if st.button("Scrape Data"):
        if username:
            with st.spinner("Scraping data..."):
                user_info, videos, images = scrape_user(username)
            display_user_info(user_info)
            display_media(videos, "video")
            display_media(images, "image")
        else:
            st.error("Please enter a valid username")

# Run the app
if __name__ == "__main__":
    main()
