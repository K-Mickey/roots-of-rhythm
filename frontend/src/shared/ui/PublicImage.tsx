'use client';

import { Image, Text } from '@mantine/core';
import { useEffect, useState } from 'react';

import type { components } from '@/api/schema';

type PublicImageView = components['schemas']['PublicImageView'];

type ImageStatus = 'pending' | 'ready' | 'broken';

export function PublicImage({ image }: { image: PublicImageView }) {
  const [status, setStatus] = useState<ImageStatus>('pending');

  useEffect(() => {
    let cancelled = false;
    const probe = new window.Image();
    probe.onload = () => {
      if (!cancelled) {
        setStatus('ready');
      }
    };
    probe.onerror = () => {
      if (!cancelled) {
        setStatus('broken');
      }
    };
    probe.src = image.url;
    return () => {
      cancelled = true;
    };
  }, [image.url]);

  // No <img> in SSR / pending / broken: avoids browser broken-icon without JS.
  if (status !== 'ready') {
    return null;
  }

  return (
    <>
      <Image
        src={image.url}
        alt={image.alt_text}
        w="100%"
        h="auto"
        fit="contain"
        onError={() => setStatus('broken')}
      />
      {image.attribution_text !== null ? (
        <Text size="xs" c="pastel.8" mt="xs">
          {image.attribution_text}
        </Text>
      ) : null}
    </>
  );
}
