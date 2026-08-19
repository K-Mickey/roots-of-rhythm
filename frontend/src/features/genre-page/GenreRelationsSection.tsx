'use client';

import { Anchor, Paper, Stack, Text, Title } from '@mantine/core';
import Link from 'next/link';

import type { components } from '@/api/schema';
import type { GenreRelations } from '@/shared/api/genre';

import {
  evidenceRoleLabel,
  evidenceStatusLabel,
  relationPerspectiveLabel,
  sourceCitationIndex,
} from './labels';

type Relation = components['schemas']['GenreRelationView'];
type Source = components['schemas']['SourceView'];

export function GenreRelationsSection({
  relations,
  sources,
}: {
  relations: GenreRelations['relations'];
  sources: Source[];
}) {
  if (relations.length === 0) {
    return null;
  }

  return (
    <Stack
      gap="md"
      component="section"
      aria-labelledby="genre-relations-heading"
    >
      <Title order={2} id="genre-relations-heading">
        Связи
      </Title>
      <Stack
        gap="md"
        component="ul"
        style={{ listStyle: 'none', padding: 0, margin: 0 }}
      >
        {relations.map((relation) => (
          <RelationCard
            key={relation.id}
            relation={relation}
            sources={sources}
          />
        ))}
      </Stack>
    </Stack>
  );
}

function RelationCard({
  relation,
  sources,
}: {
  relation: Relation;
  sources: Source[];
}) {
  const label = relationPerspectiveLabel(
    relation.relation_type,
    relation.perspective,
  );

  return (
    <Paper
      component="li"
      p="md"
      bg="pastel.0"
      shadow="xs"
      withBorder
      style={{ borderColor: 'var(--mantine-color-pastel-4)' }}
    >
      <Stack gap="sm">
        <Text fw={600}>
          {label} —{' '}
          <Anchor
            component={Link}
            href={`/genres/${encodeURIComponent(relation.related_genre.id)}`}
            c="pastel.7"
            underline="always"
          >
            {relation.related_genre.name}
          </Anchor>
        </Text>
        <Text>{relation.explanation}</Text>
        <Text size="sm" c="pastel.8">
          {relation.temporal_context.label}
        </Text>
        <Text size="sm" c="pastel.8">
          {relation.geographic_context.summary}
        </Text>
        <Text>
          <Text span fw={600}>
            Статус:{' '}
          </Text>
          {evidenceStatusLabel(relation.evidence_status)}
        </Text>
        {relation.evidence_references.length > 0 ? (
          <Stack
            gap="xs"
            component="ul"
            style={{ listStyle: 'none', padding: 0, margin: 0 }}
          >
            {relation.evidence_references.map((reference, index) => {
              const marker = sourceCitationIndex(reference.source_id, sources);
              const role = evidenceRoleLabel(reference.role);
              const locator =
                reference.locator_text ?? reference.external_url ?? null;

              return (
                <Text
                  component="li"
                  key={`${reference.source_id}-${index}`}
                  size="sm"
                >
                  {marker !== null ? (
                    <Anchor
                      href={`#source-${reference.source_id}`}
                      c="pastel.7"
                    >
                      [{marker}]
                    </Anchor>
                  ) : (
                    <Text span c="pastel.8">
                      [?]
                    </Text>
                  )}{' '}
                  <Text span>{role}</Text>
                  {locator !== null ? (
                    <>
                      {': '}
                      {reference.external_url !== null ? (
                        <Anchor
                          href={reference.external_url}
                          c="pastel.7"
                          target="_blank"
                          rel="noreferrer"
                        >
                          {locator}
                        </Anchor>
                      ) : (
                        <Text span>{locator}</Text>
                      )}
                    </>
                  ) : null}
                </Text>
              );
            })}
          </Stack>
        ) : null}
      </Stack>
    </Paper>
  );
}
