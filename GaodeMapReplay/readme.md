
## 功能
1. 导出两步路的kml轨迹
2. 使用轨迹和拍照的视频， 在高德地图web上进行回放

## 使用

1. 在index.html中替换你的高德api的key和秘钥  
https://lbs.amap.com/api/javascript-api/guide/abc/prepare
```html
<script type="text/javascript">
        window._AMapSecurityConfig = {
            securityJsCode:'您申请的安全密钥',
        }
</script>
<script type="text/javascript" src="https://webapi.amap.com/maps?v=1.4.15&key=您申请的key值"></script> 
```

2. kml文件和视频数据放在data下的一个文件夹下
```
妙峰山-20220423
├── 2022-04-23-1300北京门头沟区.kml
├── IMG_20220423_130443.jpg
├── IMG_20220423_171724.jpg
├── IMG_20220423_173013.jpg
├── IMG_20220423_174223.jpg
├── IMG_20220423_174544.jpg
├── infos.json
└── VID_20220423_160001.mp4
```

3. 使用python来生成infos.json文件
```python
    python main.py --folder=data/妙峰山-20220423
```

4. 使用vscode的live server开始index.html看效果，右键会开始动画

