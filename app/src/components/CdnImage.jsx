import { useState } from 'react';
import { staticImageSources } from '../data/ossUrls.js';

/** Small portraits use resized OSS images; an unavailable CDN falls back once. */
export default function CdnImage({ src, imageWidth = 192, preferLocal = false, ...props }) {
  return <ImageRequest key={`${src}:${imageWidth}:${preferLocal}`} src={src} imageWidth={imageWidth} preferLocal={preferLocal} {...props} />;
}

function ImageRequest({ src, imageWidth, preferLocal, onError, ...props }) {
  const [useFallback, setUseFallback] = useState(false);
  const remote = staticImageSources(src, imageWidth);
  const sources = preferLocal && import.meta.env.DEV ? { primary: src, fallback: remote.primary } : remote;
  return <img {...props} src={useFallback ? sources.fallback : sources.primary} onError={event => {
    if (!useFallback && sources.fallback !== sources.primary) setUseFallback(true);
    else onError?.(event);
  }} />;
}
