import type { components } from '@/api/schema';

type RelationType = components['schemas']['GenreRelationType'];
type Perspective = components['schemas']['RelationPerspective'];
type EvidenceStatus = components['schemas']['EvidenceStatus'];
type EvidenceRole = components['schemas']['EvidenceRole'];

const RELATION_LABELS: Record<
  RelationType,
  { subject: string; target: string; symmetric: string }
> = {
  influenced: {
    subject: 'Повлиял на',
    target: 'Влияние со стороны',
    symmetric: 'Повлиял на',
  },
  contributed_to_emergence_of: {
    subject: 'Участвовал в формировании',
    target: 'Источники формирования',
    symmetric: 'Участвовал в формировании',
  },
  developed_from: {
    subject: 'Развился из',
    target: 'Дальнейшее развитие',
    symmetric: 'Развился из',
  },
  overlaps_with: {
    subject: 'Пересекается с',
    target: 'Пересекается с',
    symmetric: 'Пересекается с',
  },
  revival_of: {
    subject: 'Возрождение традиции',
    target: 'Позднейшее возрождение',
    symmetric: 'Возрождение традиции',
  },
};

const EVIDENCE_STATUS_LABELS: Record<EvidenceStatus, string> = {
  supported: 'Подтверждено источниками',
  unverified: 'Пока не подтверждено источниками',
  disputed: 'Есть существенные разногласия',
};

const EVIDENCE_ROLE_LABELS: Record<EvidenceRole, string> = {
  supports: 'подтверждает',
  opposes: 'оспаривает',
  context: 'контекст',
};

export function relationPerspectiveLabel(
  relationType: RelationType,
  perspective: Perspective,
): string {
  return RELATION_LABELS[relationType][perspective];
}

export function evidenceStatusLabel(status: EvidenceStatus): string {
  return EVIDENCE_STATUS_LABELS[status];
}

export function evidenceRoleLabel(role: EvidenceRole): string {
  return EVIDENCE_ROLE_LABELS[role];
}

export function sourceCitationIndex(
  sourceId: string,
  sources: ReadonlyArray<{ id: string }>,
): number | null {
  const index = sources.findIndex((source) => source.id === sourceId);
  return index >= 0 ? index + 1 : null;
}
