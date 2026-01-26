// hello.cpp : 此文件包含 "main" 函数。程序执行将在此处开始并结束。
//

#include <opencv2/opencv.hpp>
#include <iostream>
#include "TestDemo.h"

int main(int argc, char** argv) {

	cv::Mat img = cv::imread("D:/image/tifa_1.jpeg");	// 读取图像
	if (img.empty())
	{
		std::cout << "Could not open or find the image" << std::endl;
		return -1;
	}
	cv::namedWindow("Image", cv::WINDOW_FREERATIO);	// 创建一个窗口，窗口名为"Image"，窗口属性为自由比例
	cv::imshow("Image", img);						// 显示图像，显示在"Image"窗口上
	

	TestDemo testDemo;								// 创建一个 TestDemo 类对象
	testDemo.colorSpace_demo(img);					// 调用 TestDemo 类的 colorSpace_demo 函数
	
	cv::waitKey(0);									// 等待按键，0表示无限等待。参数为等待时间，单位为ms
	cv::destroyAllWindows();						// 销毁所有窗口
	return 0;
}

// 运行程序: Ctrl + F5 或调试 >“开始执行(不调试)”菜单
// 调试程序: F5 或调试 >“开始调试”菜单

// 入门使用技巧: 
//   1. 使用解决方案资源管理器窗口添加/管理文件
//   2. 使用团队资源管理器窗口连接到源代码管理
//   3. 使用输出窗口查看生成输出和其他消息
//   4. 使用错误列表窗口查看错误
//   5. 转到“项目”>“添加新项”以创建新的代码文件，或转到“项目”>“添加现有项”以将现有代码文件添加到项目
//   6. 将来，若要再次打开此项目，请转到“文件”>“打开”>“项目”并选择 .sln 文件
