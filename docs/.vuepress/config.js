module.exports = {
  title: "Course Crawler",
  description: "基于 Python 3 的 MOOC 课程下载工具",
  base: "/course-crawler/",

  // 插件
  plugins: [
    // 页面滚动时自动激活侧边栏链接
    "@vuepress/active-header-links"
  ],

  // 主题配置
  themeConfig: {
    nav: [
      { text: "指南", link: "/" },
      { text: "分类", link: "/courses/icourse163" },
      { text: "进阶", link: "/advance/cli" }
    ],
    sidebarDepth: 1,
    sidebar: {
      "/advance/": ["cli", "patch"],
      "/courses/": [
        "icourse163",
        "study_163",
        "study_mooc",
        "open_163",
        "icourses",
        "xuetangx",
        "cnmooc",
        "livedu"
      ],
      "/": [
        "",
        "guide/getting-started",
        "guide/basic",
        "guide/faq",
        "guide/known-issues",
        "guide/notice"
      ]
    },

    // algolia: {
    //   apiKey: "20560f10044e76d7f16908746c3adeb1",
    //   indexName: "siguremo_course-crawler"
    // },

    lastUpdated: "Last Updated", // string | boolean

    // 假定是 GitHub. 同时也可以是一个完整的 GitLab URL
    repo: "SigureMo/course-crawler",
    // 自定义仓库链接文字。默认从 `themeConfig.repo` 中自动推断为
    // "GitHub"/"GitLab"/"Bitbucket" 其中之一，或是 "Source"。
    repoLabel: "GitHub",

    // 以下为可选的编辑链接选项

    // 假如你的文档仓库和项目本身不在一个仓库：
    docsRepo: "SigureMo/course-crawler",
    // 假如文档不是放在仓库的根目录下：
    docsDir: "docs/",
    // 假如文档放在一个特定的分支下：
    // docsBranch: "docs",
    // 默认是 false, 设置为 true 来启用
    editLinks: true,
    // 默认为 "Edit this page"
    editLinkText: "在GitHub上编辑此页！",
    // Service Worker 的配置
    serviceWorker: {
      updatePopup: true
    }
  }
};
