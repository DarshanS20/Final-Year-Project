
"""
Created on Tue Nov 3 17:32:08 2020
@author: apramanik
"""
import re 
import numpy as np
import SimpleITK as sitk
import torch
from torch.utils.data import Dataset, DataLoader
import matplotlib.pyplot as plt
import tkinter as tk
import cv2

# Tkinter GUI code here

# Functions

def normalize_img(img):
    img = img.copy().astype(np.float32)
    img -= np.mean(img)
    img /= np.std(img)
    return img


def crop_img(img):
    sizex = 144
    sizey = 144
    sizez = 8
    img = img.copy()
    sh = img.shape
    midptx = int(sh[2] / 2)
    midpty = int(sh[3] / 2)
    if sh[1] < 8:
        residue = 8 - sh[1]
        a = np.zeros((sh[0], int(residue), 144, 144), dtype=np.float32)
        img = img[:, :, midptx - int(sizex / 2):midptx + int(sizex / 2),
              midpty - int(sizey / 2):midpty + int(sizey / 2)]
        img = np.concatenate((img, a), axis=1)
    else:
        midptz = int(sh[1] / 2)
        img = img[:, midptz - int(sizez / 2):midptz + int(sizez / 2), midptx - int(sizex / 2):midptx + int(sizex / 2),
              midpty - int(sizey / 2):midpty + int(sizey / 2)]
    return img


def crop_label(img):
    sizex = 144
    sizey = 144
    sizez = 8
    img = img.copy()
    sh = img.shape
    midptx = int(sh[1] / 2)
    midpty = int(sh[2] / 2)
    if sh[0] < 8:
        residue = 8 - sh[0]
        a = np.zeros((int(residue), 144, 144), dtype=np.float32)
        img = img[:, midptx - int(sizex / 2):midptx + int(sizex / 2), midpty - int(sizey / 2):midpty + int(sizey / 2)]
        img = np.concatenate((img, a), axis=0)
    else:
        midptz = int(sh[0] / 2)
        img = img[midptz - int(sizez / 2):midptz + int(sizez / 2), midptx - int(sizex / 2):midptx + int(sizex / 2),
              midpty - int(sizey / 2):midpty + int(sizey / 2)]
    return img


def crop_img_paper(img):
    sizez = 8
    img = img.copy()
    sh = img.shape
    if sh[1] < 8:
        residue = 8 - sh[1]
        a = np.zeros((sh[0], int(residue), sh[2], sh[3]), dtype=np.float32)
        img = np.concatenate((img, a), axis=1)
    else:
        midptz = int(sh[1] / 2)
        img = img[:, midptz - int(sizez / 2):midptz + int(sizez / 2), :, :]
    return img


def crop_label_paper(img):
    sizez = 8
    img = img.copy()
    sh = img.shape
    if sh[0] < 8:
        residue = 8 - sh[0]
        a = np.zeros((int(residue), sh[1], sh[2]), dtype=np.float32)
        img = np.concatenate((img, a), axis=0)
    else:
        midptz = int(sh[0] / 2)
        img = img[midptz - int(sizez / 2):midptz + int(sizez / 2), :, :]
    return img
#IMG_DIR = "G:/ENGINEERING/FOURTH-YEAR-ENGG/New-folder/Weights/ANIKPRAM-CARDIAC_CINE_MRI_SEG"
IMG_DIR = "/Users/darshan/Documents/Engineering/8th-Semester/FrontEnd/ACDC/database/training"

class cardiacdata(Dataset):

    def __init__(self, folder_name):
        ptnum = re.findall(r'\d+', folder_name)[0].zfill(3)
        img_dir = IMG_DIR + '/patient' + ptnum + '/patient' + ptnum + '_4d.nii.gz'
        dummy_img = sitk.GetArrayFromImage(sitk.ReadImage(img_dir))
        dummy_img = crop_img(dummy_img)
        #image = cv2.imread(img_dir, cv2.IMREAD_ANYDEPTH)
        #dummy_img = crop_img(image) 

        file = open(IMG_DIR + '/patient' + ptnum + '/' + "Info.cfg", "r")
        es = int(file.read().split("\n")[1].split(":")[1])
        es_str = str(es).zfill(2)
        gt_dir_es = IMG_DIR + '/patient' + ptnum + '/patient' + ptnum + '_frame' + es_str + '_gt.nii.gz'
        es_label = sitk.GetArrayFromImage(sitk.ReadImage(gt_dir_es))
        es_label = crop_label(es_label)
        #image2 = cv2.imread(gt_dir_es, cv2.IMREAD_ANYDEPTH)
        #es_label = crop_label(image2) 

        file = open(IMG_DIR + '/patient' + ptnum + '/' + "Info.cfg", "r")
        ed = int(file.read().split("\n")[0].split(":")[1])
        ed_str = str(ed).zfill(2)
        gt_dir_ed = IMG_DIR + '/patient' + ptnum + '/patient' + ptnum + '_frame' + ed_str + '_gt.nii.gz'
        ed_label = sitk.GetArrayFromImage(sitk.ReadImage(gt_dir_ed))
        ed_label = crop_label(ed_label)
        #image3 = cv2.imread(gt_dir_ed, cv2.IMREAD_ANYDEPTH)
        #ed_label = crop_label(image2) 

        a = dummy_img[ed - 1:ed]
        b = dummy_img[es - 1:es]
        dummy_img = np.concatenate((a, b), axis=0)
        dummy_img = normalize_img(dummy_img)

        ed_label = np.expand_dims(ed_label, axis=0)
        es_label = np.expand_dims(es_label, axis=0)
        dummy_gt = np.concatenate((ed_label, es_label), axis=0)

        self.img = np.expand_dims(
            np.reshape(dummy_img, [dummy_img.shape[0] * dummy_img.shape[1], dummy_img.shape[2], dummy_img.shape[3]]),
            axis=0)
        self.gt = np.expand_dims(
            np.reshape(dummy_gt, [dummy_gt.shape[0] * dummy_gt.shape[1], dummy_gt.shape[2], dummy_gt.shape[3]]), axis=0)
        self.len = self.img.shape[0]

    def __len__(self):
        return self.len

    def __getitem__(self, i):
        img = self.img[i]
        gt = self.gt[i]

        img = torch.from_numpy(img.astype(np.float32)).unsqueeze(0)
        gt = torch.from_numpy(gt.astype(np.float32)).long()

        return img, gt


# Main Tkinter application code here

if __name__ == "__main__":
    dataset = cardiacdata()
    loader = DataLoader(dataset, shuffle=False, batch_size=1)
    count = 0
    for step, (img, gt) in enumerate(loader):
        count += 1
        print('img shape is:', img.shape)
        print('gt shape is:', gt.shape)
        fig, axes = plt.subplots(1, 2)
        pos = axes[0].imshow(img[0, 0, 2,])
        pos = axes[1].imshow(gt[0, 2,])
        plt.show()
        # break
