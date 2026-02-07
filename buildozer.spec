[app]
title = KURA PAK Tool
package.name = kurapaktool
package.domain = org.kura
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,ttf
requirements = python3,kivy,pycryptodome,zstandard
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.sdk = 23
android.ndk = 23b
android.arch = arm64-v8a,armeabi-v7a
orientation = portrait
fullscreen = 0
presplash.filename = %(source.dir)s/assets/presplash.png
icon.filename = %(source.dir)s/assets/icon.png
version = 1.0.0
