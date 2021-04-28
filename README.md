# micropython-actions
Build micropython firmware with github actions

ESP32编译添加CMODULES，需要在build-with里面填写下面的代码。
USER_C_MODULES=/home/runner/work/micropython-actions/micropython-actions/cmodule all

ESP32烧写固件使用firmware.bin，烧写到0x1000地址


参考资料：
https://docs.github.com/cn/actions/reference/events-that-trigger-workflows
https://p3terx.com/archives/github-actions-manual-trigger.html
http://www.ruanyifeng.com/blog/2019/09/getting-started-with-github-actions.html

