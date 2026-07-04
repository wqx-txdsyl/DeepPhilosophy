/**
 * Icon 组件 —— PNG 图标（lazy load + 浏览器缓存）
 * <Icon name="nav-books" size={20} />
 */
function Icon({ name, size = 20, style, className, ...props }) {
  return (
    <img
      src={`/icons/${name}.png`}
      alt=""
      loading="lazy"
      {...props}
      className={className}
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
