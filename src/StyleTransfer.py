'''
Credit: jimmyyhwu on GitHub: https://github.com/jimmyyhwu/
style-transfer/blob/master/main.py

Incorporated generator to yield each time a new iteration have been completed
'''
from functools import reduce
import cv2
import numpy as np
import os
import skimage.io
import tensorflow as tf

import vgg19

CONTENT_LAYER = 'conv4_2'
STYLE_LAYERS = ['conv1_1', 'conv2_1', 'conv3_1', 'conv4_1', 'conv5_1']

ALPHA = 1.0
BETA = 50.0
LR = 1.0


def load_image(PATH):
    img = skimage.io.imread(PATH)
    yuv = cv2.cvtColor(np.float32(img), cv2.COLOR_RGB2YUV)
    img = img - vgg19.VGG_MEAN
    img = img[:, :, (2, 1, 0)]  # rgb to bgr
    return img[np.newaxis, :, :, :], yuv


def save_image(img, PATH, content_yuv=None):
    img = np.squeeze(img)
    img = img[:, :, (2, 1, 0)]  # bgr to rgb
    img = img + vgg19.VGG_MEAN
    if content_yuv is not None:
        yuv = cv2.cvtColor(np.float32(img), cv2.COLOR_RGB2YUV)
        yuv[:, :, 1:3] = content_yuv[:, :, 1:3]
        img = cv2.cvtColor(yuv, cv2.COLOR_YUV2RGB)
    img = np.clip(img, 0, 255).astype(np.uint8)
    skimage.io.imsave(PATH, img)


def feature_to_gram(f):
    shape = f.get_shape()
    n_channels = shape[3].value
    size = np.prod(shape).value
    f = tf.reshape(f, [-1, n_channels])
    return tf.matmul(tf.transpose(f), f) / size


def get_style_rep(vgg):
    return list(map(feature_to_gram, map(lambda l: getattr(vgg, l),
                                         STYLE_LAYERS)))


def compute_style_loss(style_rep, image_vgg):
    style_losses = list(map(
        tf.nn.l2_loss, [a - b for (a, b) in zip(style_rep, get_style_rep
                                                (image_vgg))]))
    style_losses = [style_losses[i] / (style_rep[i].size)
                    for i in range(len(style_losses))]
    return reduce(tf.add, style_losses)


def style_transfer(content_path, style_path, output_dir="output",
                   iterations=1000, vgg_path='vgg19.npy', preserve_color=True):
    # mean subtract input images
    content_img, content_yuv = load_image(content_path)
    style_img, _ = load_image(style_path)

    # obtain content and style reps
    with tf.Session() as sess:
        content_vgg = vgg19.Vgg19(vgg_path)
        content = tf.placeholder("float", content_img.shape)
        content_vgg.build(content)
        style_vgg = vgg19.Vgg19(vgg_path)
        style = tf.placeholder("float", style_img.shape)
        style_vgg.build(style)

        sess.run(tf.global_variables_initializer())
        content_rep = sess.run(getattr(content_vgg, CONTENT_LAYER), feed_dict={
                               content: content_img})
        style_rep = sess.run(get_style_rep(style_vgg),
                             feed_dict={style: style_img})

    # start with white noise
    noise = tf.truncated_normal(
        content_img.shape, stddev=0.1 * np.std(content_img))
    image = tf.Variable(noise)
    image_vgg = vgg19.Vgg19(vgg_path)
    image_vgg.build(image)

    # define losses and optimizer
    content_loss = tf.nn.l2_loss(
        getattr(image_vgg, CONTENT_LAYER) - content_rep) / content_rep.size
    style_loss = compute_style_loss(style_rep, image_vgg)
    loss = ALPHA * content_loss + BETA * style_loss
    optimizer = tf.train.AdamOptimizer(LR).minimize(loss)

    # style transfer
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        for i in range(1, iterations + 1):
            sess.run(optimizer)
            fmt_str = 'Iteration {:4}/{:4} content loss {:14} style loss {:14}'
            print(fmt_str.format(i, iterations, ALPHA *
                                 content_loss.eval(),
                                 BETA * style_loss.eval()))

            # undo mean subtract and save output image
            output_path = os.path.join(
                output_dir, 'output_{:04}.jpg'.format(i))
            save_image(image.eval(), output_path,
                       content_yuv if preserve_color else None)
            yield
