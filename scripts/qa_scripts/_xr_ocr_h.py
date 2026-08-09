def human(s):
    if s < 60:
        return '%.0f 秒' % s
    if s < 3600:
        return '%.0f 分' % (s / 60)
    return '%.1f 小时' % (s / 3600)
