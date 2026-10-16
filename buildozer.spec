[app]

# (str) 应用显示名称
title = 股票状态栏助手

# (str) 应用包名（只能用小写字母、数字和下划线）
package.name = stocktickerapp

# (str) 包域名
package.domain = org.myapp

# (str) 源代码所在目录（. 代表当前目录）
source.dir = .

# (list) 打包时包含的文件扩展名
source.include_exts = py,png,jpg,kv,atlas

# (str) 应用版本号
version = 1.0.0

# (list) 应用依赖库（必须包含 python3 和 kivy）
requirements = python3,kivy,requests,cython==0.29.36

# (list) Android 需要的权限（获取网络数据必须开启 INTERNET）
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# (str) 屏幕方向（portrait=竖屏, landscape=横屏, all=自动）
orientation = portrait

# (bool) 是否全屏（True=全屏隐藏状态栏, 0=显示状态栏）
fullscreen = 0


# 指定稳定的 NDK 版本
android.ndk = 25b

# (str) 应用图标（如果暂时没有图标，可以注释掉这行）
# icon.filename = icon.png

# (str) 启动画面（如果暂时没有，可以注释掉这行）
# presplash.filename = presplash.png

[buildozer]

# (int) 日志级别（2=正常信息，3=详细调试）
log_level = 2

# (bool) 是否开启调试模式（打包测试时设为 1）
debug = 1