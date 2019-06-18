#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/1/25 11:36
# @Author  : blvin.Don
# @File    : New_detection.py

# 引入所需模块
# encoding: UTF-8
import os
import cv2
import sys
import glob as gb
import time

from socket import *
import SingleUAV.Yaw_Angke

HOST = '192.168.31.105'
PORT = 7896
s = socket(AF_INET, SOCK_DGRAM)
s.connect((HOST, PORT))


# 鼠标框选区域，用于显示鼠标轨迹
selection = None
# 框选开始
drag_start = None
# 框选完成区域即跟踪目标
track_window = None
# 跟踪开始标志
track_start = False
# 创建KCF跟踪器
tracker = cv2.TrackerKCF_create()


# 鼠标响应函数
def onmouse(event, x, y, flags, param):
    global selection, drag_start, track_window, track_start
    # 鼠标左键按下
    if event == cv2.EVENT_LBUTTONDOWN:
        drag_start = (x, y)
        track_window = None
    # 开始拖拽
    if drag_start:
        xmin = min(x, drag_start[0])
        ymin = min(y, drag_start[1])
        xmax = max(x, drag_start[0])
        ymax = max(y, drag_start[1])
        selection = (xmin, ymin, xmax, ymax)
    # 鼠标左键弹起
    if event == cv2.EVENT_LBUTTONUP:
        drag_start = None
        selection = None
        track_window = (xmin, ymin, xmax - xmin, ymax - ymin)
        if track_window and track_window[2] > 0 and track_window[3] > 0:
            track_start = True
            # 跟踪器以鼠标左键弹起时所在帧和框选区域为参数初始化
            tracker.init(frame, track_window)


def file_name(file_dir):
    L = []
    for root, dirs, files in os.walk(file_dir):
        for file in files:
            if os.path.splitext(file)[1] == '.jpg':
                L.append(int(file[:-4]))
    return max(L) - 1


# 读取视频/摄像头
# video = cv2.VideoCapture(0)
# video = cv2.VideoCapture('traffic.flv')
# 命名窗口，第二个参数表示窗口可缩放
cv2.namedWindow('KCFTracker', cv2.WINDOW_NORMAL)
# 为窗口绑定鼠标响应函数onmouse
cv2.setMouseCallback('KCFTracker', onmouse)
directory_name = "D:/UAV_image"
# img_path = gb.glob("D:/pic/UAV_image//*.jpg")
# for path in img_path"
while True:
    image = file_name("D:/UAV_image")
    # print(image)
    frame = cv2.imread("D:/UAV_image/" + str(image) + ".jpg")
    if frame is None:
        # break
        print("error")
    # 以矩形标记鼠标框选区域
    if selection:
        x0, y0, x1, y1 = selection
        cv2.rectangle(frame, (x0, y0), (x1, y1), (255, 0, 0), 2, 1)
    # 函数执行开始时间
    timer = cv2.getTickCount()

    # 更新跟踪器得到最新目标区域
    track_ok = None
    if track_start:
        track_ok, bbox = tracker.update(frame)

    # 计算fps
    fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer)

    # 画出目标最新边界区域
    # 如果跟踪成功
    if track_ok:
        p1 = (int(bbox[0]), int(bbox[1]))
        p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))

        cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
        print(int(bbox[0] + bbox[2] / 2), int(bbox[1] + bbox[3] / 2))
        angle = SingleUAV.Yaw_Angke.simple_angle([int(bbox[0] + bbox[2] / 2), int(bbox[1] + bbox[3] / 2)],[598, 288])
        print("角度：", angle)
        message = str(str(0) + ',' + str(0.1) + ',' + str(angle) + ',' + str(4))
        s.sendall(message.encode('utf-8'))
        # data = s.recv(1024)
        print("检测到目标，已发送：", str(str(0) + ',' + str(0.1) + ',' + str(angle) + ',' + str(4)))
    elif not track_start:
        cv2.putText(frame, "No tracking target selected", (100, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

    elif not track_ok:
        cv2.putText(frame, "Tracking failure detected", (100, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
        message = str(str(0) + ',' + str(0) + ',' + str(0) + ',' + str(0))
        s.sendall(message.encode('utf-8'))
        # data = s.recv(1024)
        print("目标丢失，已发送：", str(str(0) + ',' + str(0) + ',' + str(0) + ',' + str(0)))

    # 显示提示信息
    cv2.putText(frame, "KCF Tracker", (100, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50, 170, 50), 2)
    cv2.putText(frame, "FPS : " + str(int(fps)), (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50, 170, 50), 2)
    # 显示结果
    cv2.imshow("KCFTracker", frame)
    # 按ESC退出
    k = cv2.waitKey(100) & 0xff
    if k == 27:
        break
    time.sleep(0.1)
cv2.destroyAllWindows()