# 网易云课堂 MOOC

## 简介

[网易云课堂 MOOC 课程](http://mooc.study.163.com/) 有一部分中国大学 MOOC 的内容，此外还有一些微专业内容，但是很多需要付费，推荐 [顶尖中文大学计算机专业课程体系](https://study.163.com/curricula/cs.htm) 与 [深度学习工程师微专业](https://mooc.study.163.com/smartSpec/detail/1001319001.htm)

## 地址格式

课程的地址必须类似以下两种格式

```
http://mooc.study.163.com/course/2001281002#/info
http://mooc.study.163.com/course/2001281002
```

::: tip

-  上面的 `course` 替换为 `learn` 也是支持的
   :::

## 碎碎念

与[中国大学 MOOC](./icourse163.md) 大体上相同，但它对身份的验证比较苛刻，你**本身无法访问到的内容程序也是无法帮你获取的，也就是说它并不能帮你获取你未参加的已关闭学期的内容**

Cookies 极易失效，可在运行时添加参数 `-c` 注入新的 Cookies
