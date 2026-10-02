import { useState } from 'react';
import { staticImageSources } from '../data/ossUrls.js';

/** Small portraits use resized OSS images; an unavailable CDN falls back once. */
export default function CdnImage({ src, imageWidth = 192, ...props }) {
  return <ImageRequest key={`${src}:${imageWidth}`} src={src} imageWidth={imageWidth} {...props} />;
}

function ImageRequest({ src, imageWidth, onError, ...props }) {
  const [useFallback, setUseFallback] = useState(false);
  const sources = staticImageSources(src, imageWidth);
  return <img {...props} src={useFallback ? sources.fallback : sources.primary} onError={event => {
    if (!useFallback && sources.fallback !== sources.primary) setUseFallback(true);
    else onError?.(event);
  }} />;
}
