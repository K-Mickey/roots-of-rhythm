'use client';

import { Badge, Stack, Tabs, Text, Title } from '@mantine/core';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useEffect } from 'react';

import type { RecordingOverview } from '@/shared/api/recording';
import type { SongOverview } from '@/shared/api/song';

import {
  formatLyricsVersionLabel,
  formatLyricsVersionShortLabels,
  resolveSelectedLyricsVersionId,
} from './labels';

type LyricsVersion =
  RecordingOverview['lyrics'][number] | SongOverview['lyrics_versions'][number];

export function RecordingLyricsSection({
  versions,
  selectedId,
  headingOrder = 2,
  normalizeQuery = false,
}: {
  versions: LyricsVersion[];
  selectedId?: string | null;
  headingOrder?: 2 | 3;
  normalizeQuery?: boolean;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const requestedId =
    selectedId === undefined ? searchParams.get('text') : selectedId;
  const selectedVersionId = resolveSelectedLyricsVersionId(
    versions,
    requestedId,
  );
  const labels = formatLyricsVersionShortLabels(versions);

  useEffect(() => {
    if (
      !normalizeQuery ||
      selectedVersionId === null ||
      requestedId === selectedVersionId
    ) {
      return;
    }
    const params = new URLSearchParams(searchParams.toString());
    params.set('text', selectedVersionId);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  }, [
    normalizeQuery,
    pathname,
    requestedId,
    router,
    searchParams,
    selectedVersionId,
  ]);

  if (selectedVersionId === null) {
    return null;
  }

  const select = (versionId: string | null) => {
    if (versionId === null) return;
    const params = new URLSearchParams(searchParams.toString());
    params.set('text', versionId);
    router.push(`${pathname}?${params.toString()}`, { scroll: false });
  };

  return (
    <Stack gap="sm" component="section" aria-labelledby="lyrics-heading">
      <Title order={headingOrder} id="lyrics-heading">
        Текст
      </Title>
      <Tabs value={selectedVersionId} onChange={select} keepMounted={false}>
        <Tabs.List
          aria-label="Версии текста"
          style={{ flexWrap: 'nowrap', maxWidth: '100%', overflowX: 'auto' }}
        >
          {versions.map((version, index) => {
            const fullLabel = formatLyricsVersionLabel(version);
            return (
              <Tabs.Tab
                key={version.id}
                value={version.id}
                aria-label={fullLabel}
                title={fullLabel}
                style={{ flex: '0 0 auto' }}
              >
                {labels[index]}
                {version.creation_method === 'machine_translation' ? (
                  <Badge ml="xs" size="xs">
                    Машинный перевод
                  </Badge>
                ) : null}
              </Tabs.Tab>
            );
          })}
        </Tabs.List>
        {versions.map((version) => (
          <Tabs.Panel key={version.id} value={version.id} pt="md">
            {'confirmed_for_recording' in version &&
            !version.confirmed_for_recording &&
            version.body !== null ? (
              <Text size="sm" mb="xs">
                Соответствие текста этой записи не подтверждено
              </Text>
            ) : null}
            {version.body !== null ? (
              <Text style={{ whiteSpace: 'pre-wrap' }}>{version.body}</Text>
            ) : (
              <Text c="pastel.8">
                {version.body_unavailable_reason ??
                  'Текст недоступен для просмотра.'}
              </Text>
            )}
          </Tabs.Panel>
        ))}
      </Tabs>
    </Stack>
  );
}
