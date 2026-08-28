'use client';

import {
  Anchor,
  Container,
  Skeleton,
  Stack,
  Tabs,
  Text,
  Title,
} from '@mantine/core';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect } from 'react';

import type { SongOverview } from '@/shared/api/song';

import {
  formatLyricsVersionTabLabel,
  formatPeriod,
  formatWorkCreditRole,
  formatWorkRelationType,
  hasPeriodBounds,
  resolveSelectedLyricsVersionId,
  safeExternalHref,
} from './labels';

export function SongPageContent({ song }: { song: SongOverview }) {
  const aliases = song.aliases;
  const identities = song.external_identities;
  const songPeriod = hasPeriodBounds(song.period)
    ? formatPeriod(song.period)
    : null;
  const lyricsVersions = song.lyrics_versions;

  return (
    <Container size="52rem" py="xl" style={{ containerType: 'inline-size' }}>
      <Stack gap="xl" component="article">
        <Stack gap="md" component="section">
          <Title order={1}>{song.name}</Title>
          {aliases.length > 0 ? (
            <Text c="pastel.8" size="sm">
              Также известна как: {aliases.join(', ')}
            </Text>
          ) : null}
          {songPeriod !== null ? (
            <Text c="pastel.8" size="sm">
              Период: {songPeriod}
            </Text>
          ) : null}
          {song.description !== null ? <Text>{song.description}</Text> : null}
        </Stack>

        {identities.length > 0 ? (
          <Stack
            gap="sm"
            component="section"
            aria-labelledby="identities-heading"
          >
            <Title order={2} id="identities-heading">
              Внешние идентификаторы
            </Title>
            <Stack
              gap="xs"
              component="ul"
              style={{ paddingInlineStart: '1.25rem', margin: 0 }}
            >
              {identities.map((identity) => {
                const href =
                  identity.url === null ? null : safeExternalHref(identity.url);
                const label = `${identity.provider}: ${identity.identifier}`;

                return (
                  <li key={`${identity.provider}:${identity.identifier}`}>
                    {href !== null ? (
                      <Anchor
                        href={href}
                        c="pastel.7"
                        underline="always"
                        target="_blank"
                        rel="noreferrer"
                      >
                        {label}
                      </Anchor>
                    ) : (
                      <Text>{label}</Text>
                    )}
                  </li>
                );
              })}
            </Stack>
          </Stack>
        ) : null}

        {song.credits.length > 0 ? (
          <Stack gap="sm" component="section" aria-labelledby="authors-heading">
            <Title order={2} id="authors-heading">
              Авторы
            </Title>
            <Stack
              gap="xs"
              component="ul"
              style={{ paddingInlineStart: '1.25rem', margin: 0 }}
            >
              {song.credits.map((credit) => {
                const roleLabel = formatWorkCreditRole(credit.role);
                const creditedAs =
                  credit.credited_as !== null
                    ? ` (как ${credit.credited_as})`
                    : '';

                return (
                  <li
                    key={`${credit.person.id}:${credit.role}:${credit.credited_as ?? ''}`}
                  >
                    <Anchor
                      component={Link}
                      href={`/performers/${encodeURIComponent(credit.person.id)}`}
                      c="pastel.7"
                      underline="always"
                    >
                      {credit.person.name}
                    </Anchor>
                    {creditedAs}
                    {' — '}
                    {roleLabel}
                  </li>
                );
              })}
            </Stack>
          </Stack>
        ) : null}

        {song.classifications.length > 0 ? (
          <Stack
            gap="sm"
            component="section"
            aria-labelledby="classifications-heading"
          >
            <Title order={2} id="classifications-heading">
              Классификация произведения
            </Title>
            <Stack
              gap="xs"
              component="ul"
              style={{ paddingInlineStart: '1.25rem', margin: 0 }}
            >
              {song.classifications.map((genre) => (
                <li key={genre.id}>
                  <Anchor
                    component={Link}
                    href={`/genres/${encodeURIComponent(genre.id)}`}
                    c="pastel.7"
                    underline="always"
                  >
                    {genre.name}
                  </Anchor>
                </li>
              ))}
            </Stack>
          </Stack>
        ) : null}

        {song.related_works.length > 0 ? (
          <Stack
            gap="sm"
            component="section"
            aria-labelledby="related-works-heading"
          >
            <Title order={2} id="related-works-heading">
              Связанные произведения
            </Title>
            <Stack
              gap="xs"
              component="ul"
              style={{ paddingInlineStart: '1.25rem', margin: 0 }}
            >
              {song.related_works.map((related) => (
                <li key={`${related.relation_type}:${related.work.id}`}>
                  {formatWorkRelationType(related.relation_type)}
                  {': '}
                  <Anchor
                    component={Link}
                    href={`/songs/${encodeURIComponent(related.work.id)}`}
                    c="pastel.7"
                    underline="always"
                  >
                    {related.work.name}
                  </Anchor>
                </li>
              ))}
            </Stack>
          </Stack>
        ) : null}

        {lyricsVersions.length > 0 ? (
          <Suspense fallback={<SongLyricsSectionFallback />}>
            <SongLyricsSection versions={lyricsVersions} />
          </Suspense>
        ) : null}
      </Stack>
    </Container>
  );
}

function SongLyricsSection({
  versions,
}: {
  versions: SongOverview['lyrics_versions'];
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const textParam = searchParams.get('text');
  const selectedVersionId = resolveSelectedLyricsVersionId(versions, textParam);
  const selectedVersion =
    versions.find((version) => version.id === selectedVersionId) ?? null;

  useEffect(() => {
    if (selectedVersionId === null) {
      return;
    }
    if (textParam === selectedVersionId) {
      return;
    }
    const params = new URLSearchParams(searchParams.toString());
    params.set('text', selectedVersionId);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  }, [pathname, router, searchParams, selectedVersionId, textParam]);

  const handleTabChange = (versionId: string | null) => {
    if (versionId === null) {
      return;
    }
    const params = new URLSearchParams(searchParams.toString());
    params.set('text', versionId);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  };

  if (selectedVersion === null) {
    return null;
  }

  return (
    <Stack gap="sm" component="section" aria-labelledby="lyrics-heading">
      <Title order={2} id="lyrics-heading">
        Текст
      </Title>
      <Tabs
        value={selectedVersion.id}
        onChange={handleTabChange}
        keepMounted={false}
      >
        <Tabs.List aria-label="Версии текста">
          {versions.map((version) => (
            <Tabs.Tab
              key={version.id}
              value={version.id}
              aria-selected={version.id === selectedVersion.id}
            >
              {formatLyricsVersionTabLabel(version)}
            </Tabs.Tab>
          ))}
        </Tabs.List>

        {versions.map((version) => (
          <Tabs.Panel key={version.id} value={version.id} pt="md">
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

function SongLyricsSectionFallback() {
  return (
    <Stack
      gap="sm"
      component="section"
      aria-labelledby="lyrics-heading"
      aria-busy="true"
    >
      <Title order={2} id="lyrics-heading">
        Текст
      </Title>
      <Skeleton height={36} width="60%" />
      <Skeleton height={80} />
    </Stack>
  );
}
