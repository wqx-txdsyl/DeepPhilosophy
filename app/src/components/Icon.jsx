/**
 * Icon 组件 —— 替换 emoji，使用生成的 48px PNG 图标
 * <Icon name="nav-books" size={20} />
 */
function Icon({ name, size = 20, style, className, ...props }) {
  return (
    <img
      src={`/icons/${name}.png`}
      alt=""
      {...props}
      className={className}
      style={{
        width: size,
        height: size,
        display: 'inline-block',
        verticalAlign: 'middle',
        objectFit: 'contain',
        ...style,
      }}
    />
  );
}

export default Icon;
