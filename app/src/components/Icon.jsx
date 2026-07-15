/**
 * Icon 组件 —— PNG 图标（lazy load + 浏览器缓存 + 尺寸提示防布局偏移）
 * <Icon name="nav-books" size={20} />
 */
function Icon({ name, size = 20, style, className, ...props }) {
  return (
    <img
      src={`/icons/${name}.png`}
      alt=""
      loading="lazy"
      width={size}
      height={size}
      {...props}
      className={`icon-img${className ? ' ' + className : ''}`}
      style={{
        width: size,
        height: size,
        display: 'inline-block',
        verticalAlign: 'middle',
        flexShrink: 0,
        ...style,
      }}
    />
  );
}

export default Icon;
