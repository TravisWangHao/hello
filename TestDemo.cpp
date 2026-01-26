#include "TestDemo.h"

TestDemo::TestDemo()
{
}

TestDemo::~TestDemo()
{
}

void TestDemo::colorSpace_demo(Mat& image)
{
	cv::Mat gray, hsv, ycrcb;  // 定义三个 Mat 类对象

	//创建三个窗口，窗口名分别为"Gray"、"HSV"、"YCrCb"，窗口属性为自由比例
	cv::namedWindow("Gray", cv::WINDOW_FREERATIO);
	cv::namedWindow("HSV", cv::WINDOW_FREERATIO);
	cv::namedWindow("YCrCb", cv::WINDOW_FREERATIO);

	//转换图像颜色空间
	cv::cvtColor(image, gray, cv::COLOR_BGR2GRAY);		// 将图像转换为灰度图
	cv::cvtColor(image, hsv, cv::COLOR_BGR2HSV);		// 将图像转换为 HSV 图
	cv::cvtColor(image, ycrcb, cv::COLOR_BGR2YCrCb);	// 将图像转换为 YCrCb 图

	// 显示转换后的图像
	imshow("Gray", gray);
	imshow("HSV", hsv);
	imshow("YCrCb", ycrcb);

	// 保存转换后的图像
	cv::imwrite("D:/image/gray.jpeg", gray);
	cv::imwrite("D:/image/hsv.jpeg", hsv);
	cv::imwrite("D:/image/ycrcb.jpeg", ycrcb);

}