#pragma once
#include<opencv2/opencv.hpp>

using namespace cv;

class TestDemo
{
public:
	TestDemo();
	~TestDemo();
	void colorSpace_demo(Mat& image);	// 颜色空间转换,传入图像引用
};
