import instaloader

L = instaloader.Instaloader()


def extractShortcode(url):
    parts = url.split("/")
    return parts[4]



def main():
    #Login required
    username = "hilal.verse"
    L.load_session_from_file(username)
    print(L.test_login())

    #Getting Shortcode:
    rUrl = input("Enter your url: ")
    my_shortcode = extractShortcode(rUrl)
    print(my_shortcode)

    try:
        post = instaloader.Post.from_shortcode(L.context, my_shortcode)
        L.download_post(post, target="Reels_Download")
        print("Download succesful!")
    except Exception as e:
        print(f"An error occurred: {e}")
    

if __name__ == "__main__":
    main()

