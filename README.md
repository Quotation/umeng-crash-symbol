Umeng Crash Symbolicator
==================

一键把友盟iOS崩溃日志里的?????转成可见的symbol。

[友盟](http://www.umeng.com/)的iOS应用错误分析工具收集到的崩溃日志（Stack Trace），有些情况下无法显示出正确的symbol，显示为一堆问号?????。
使用此工具可以在浏览器中一键把问号转换成symbol和代码位置。


使用方法
--

1. 把不同版本的App Bundle和对应的dSYM放到`symbols`目录下。目录结构如下：

        + symbols
            + DemoApp-1.0
                - DemoApp.app
                - DemoApp.app.dSYM
            + DemoApp-1.1
                - DemoApp.app
                - DemoApp.app.dSYM

2. 启动服务。地址和端口可以自定义：

        python symbol_server.py localhost 8000
    
   启动成功后显示

        Server started - http://localhost:8000

3. 用浏览器里访问上一步提示的地址，把链接`Umeng Crash Symbolicator`拖到书签栏上。

4. 在使用友盟的错误分析工具页面时，点击书签栏里的`Umeng Crash Symbolicator`即可把问号转换成symbol。


原理
--

友盟的崩溃日志中记录了`dSYM UDID`，通过UDID查询到该条崩溃日志对应的App版本。[[参考1]][ref1]
再取Stack Trace里问号前面的地址，结合`Slide Address`和`Base Address`，使用`atos`命令查出symbol。[[参考2]][ref2] [[参考3]][ref3]

[ref1]: http://draftdog.blogspot.com/2012/04/figuring-out-uuid-for-dsym.html
[ref2]: http://stackoverflow.com/questions/1460892/symbolicating-iphone-app-crash-reports
[ref3]: http://stackoverflow.com/questions/13574933/ios-crash-reports-atos-not-working-as-expected/13576028#13576028

示例
--

显示错误的Stack Trace像这样：

    *** -[NSDictionary initWithDictionary:copyItems:]: dictionary argument is not an NSDictionary
    (null)
    (
    	0   CoreFoundation                      0x328632bb  + 186
    	1   libobjc.A.dylib                     0x3a70e97f objc_exception_throw + 30
    	2   CoreFoundation                      0x327efff5  + 212
    	3   CoreFoundation                      0x327eff0b  + 42
    	4   ????????????                        0x0009ff8f ???????????? + 233359
    	5   ????????????                        0x0009fefb ???????????? + 233211
    	6   ????????????                        0x001625cd ???????????? + 1029581
    	7   ????????????                        0x00163eb1 ???????????? + 1035953
    	8   Foundation                          0x330f8d41  + 200
    	9   Foundation                          0x330f05c1  + 840
    )

使用此工具转换后：

    *** -[NSDictionary initWithDictionary:copyItems:]: dictionary argument is not an NSDictionary
    (null)
    (
    	0   CoreFoundation                      0x328632bb  + 186
    	1   libobjc.A.dylib                     0x3a70e97f objc_exception_throw + 30
    	2   CoreFoundation                      0x327efff5  + 212
    	3   CoreFoundation                      0x327eff0b  + 42
    	4   ????????????                        0x0009ff8f -[BookManager getNoteSummaryDictWithBookID:] (BookManager.m:1784)
     + 233359
    	5   ????????????                        0x0009fefb -[BookManager getNoteSummaryList] (BookManager.m:1775)
     + 233211
    	6   ????????????                        0x001625cd +[DkAppURLProtocol getJsonForAllNoteSummaryWithSortType:] (DkAppURLProtocol.m:220)
     + 1029581
    	7   ????????????                        0x00163eb1 -[DkAppURLProtocol startLoading] (DkAppURLProtocol.m:495)
     + 1035953
    	8   Foundation                          0x330f8d41  + 200
    	9   Foundation                          0x330f05c1  + 840
