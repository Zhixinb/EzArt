'''
Created on Apr 2, 2018

@author: Robin
'''

from StyleTransfer import style_transfer
import numpy as np
import tkinter as tk
import os
import requests
import shutil
from ImgFetcher import img_fetcher
from PIL import ImageTk, Image

PATH = ""


class Downloader():
    def __init__(self, folder_name, img_links):
        self.img_links = img_links
        # create the directory if it does not exist
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # iterate through all the links
        for idx in range(len(img_links)):
            with open(os.path.join(folder_name, 'img_' + str(idx) +
                                   '.jpg'), 'wb') as out_file:
                img_response = requests.get(img_links[idx], stream=True)
                # if the response is good, same the content as img file
                if img_response.status_code == 200:
                    img_response.raw.decode_content = True
                    shutil.copyfileobj(img_response.raw, out_file)
                    idx += 1

    def __str__(self):
        print(self.img_links)


def run_set_up(root, artist, content):
    load_limit = 5

    # download imgs of the content
    source_url = ("https://www.rawpixel.com/search/{}?"
                  "sort=curated&premium=free&page=1"
                  )
    content_links = img_fetcher(
        PATH, source_url, query=content, load_limit=load_limit)
    Downloader(content + "/", content_links)

    print("Finished downloading contents")

    # go fetch the img link from the url
    artist_links = img_fetcher(
        PATH, source_url, query=artist, load_limit=load_limit)
    Downloader(artist + "/", artist_links)

    print("Finished downloading arts")

    style_filename = np.random.permutation([os.path.join
                                            (artist, 'img_' + str(x) + '.jpg')for x in range(load_limit)])[0]

    content_filename = np.random.permutation([os.path.join
                                              (content, 'img_' + str(x) + '.jpg')for x in range(load_limit)])[0]

    # display imgs before style transfer
    # show style image
    style_img = Image.open(style_filename)
    img1 = ImageTk.PhotoImage(style_img)
    img1 = ImageTk.PhotoImage(
        style_img.resize((img1.width() // 2, img1.height() // 2),
                         Image.ANTIALIAS))

    # show content image
    content_img = Image.open(content_filename)
    img2 = ImageTk.PhotoImage(content_img)
    img2 = ImageTk.PhotoImage(
        content_img.resize((img2.width() // 2, img2.height() // 2),
                           Image.ANTIALIAS))
    tk.Label(root, image=img1).grid(row=2, column=0, sticky=tk.S)
    tk.Label(root, image=img2).grid(row=2, column=2, sticky=tk.S)

    root.update_idletasks()
    root.update()

    style_transfer_generation(content_filename, style_filename, root)

    return


def perform_style_transfer(root, artist, content):

    # check if inputs are good
    if artist is None or content is None or artist.get() is "" or \
            content.get() is "":
        print("Please don't leave a field blank!")
        return

    run_set_up(root, artist.get(), content.get())

    print("Done")


def style_transfer_generation(content_filename, style_filename,
                              root, iterations=200):
    ''' Generates a new combination of the base images and style images of
    an artist. Returns the file name that was used for the content, style, and
    mix file
    '''
    cnt = 1
    # creating the transfer generator
    transfer = style_transfer(
        content_filename, style_filename, iterations=iterations)

    next(transfer)
    while (cnt <= iterations + 1):
        # show resulting image
        mixed_img = Image.open(os.path.join(
            'output', 'output_{:04}.jpg'.format(cnt)))
        img3 = ImageTk.PhotoImage(mixed_img)
        img3 = ImageTk.PhotoImage(
            mixed_img.resize((img3.width() // 2, img3.height() // 2),
                             Image.ANTIALIAS))
        tk.Label(root, image=img3).grid(row=2, column=3, sticky=tk.S)

        root.update_idletasks()
        root.update()

        print("Generating new mixed image")
        next(transfer)
        print("Finished generating new mixed image")

        cnt += 1


def main():

    # generate window with text field for base image and style image and
    # submit button

    root = tk.Tk()
    root.title("EzArt")
    artist_name = tk.StringVar()
    content_name = tk.StringVar()

    # artist label
    tk.Label(root, text="Artist").grid(row=0, column=0, sticky=tk.S)

    # artist entry textbox
    tk.Entry(root, textvariable=artist_name).grid(row=1, column=0, sticky=tk.N)

    # text label
    tk.Label(root, text="paints a(n)").grid(row=1, column=1, sticky=tk.W)

    # label
    tk.Label(root, text="Subject").grid(row=0, column=2, sticky=tk.S)

    # entry textbox
    tk.Entry(root, textvariable=content_name).grid(
        row=1, column=2, sticky=tk.N)

    # button
    tk.Button(root, text="Go paint!", command=lambda: perform_style_transfer(
        root, artist_name, content_name)).grid(row=1, column=3, sticky=tk.W)

    root.mainloop()


if __name__ == '__main__':
    #   get chrome driver PATH
    is_path = False
    PATH = r'C:\Users\Robin\Downloads\chromedriver.exe'
    while not is_path:
        try:
            if os.path.exists(PATH):
                is_path = True
            else:
                print("Chromedriver not found at:" +
                      str(PATH) + " please input correct directory of " +
                      "chromedriver.exe")
                PATH = input("Enter the PATH of your file: ")

        except AssertionError:
            pass
    output_folder = "output/"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    print('Saving result images to {}'.format(output_folder))
    main()
