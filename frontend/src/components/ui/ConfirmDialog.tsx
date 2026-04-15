// =============================================================================
// components/ui/ConfirmDialog.tsx — Destructive action confirmation modal (CR-10)
// Wraps Modal with a standardised confirm/cancel layout.
// isDanger prop turns the confirm button red to signal a destructive action.
// =============================================================================

import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'

interface ConfirmDialogProps {
  isOpen: boolean
  onConfirm: () => void
  onCancel: () => void
  title: string
  description: string
  // Label for the confirm button; defaults to "ยืนยัน"
  confirmLabel?: string
  // When true: confirm button uses danger (red) variant
  isDanger?: boolean
  // Whether a loading spinner should show on the confirm button (async actions)
  isLoading?: boolean
}

export function ConfirmDialog({
  isOpen,
  onConfirm,
  onCancel,
  title,
  description,
  confirmLabel = 'ยืนยัน',
  isDanger = false,
  isLoading = false,
}: ConfirmDialogProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onCancel}
      title={title}
      size="sm"
      footer={
        <>
          {/* Cancel always uses ghost variant so it never looks dangerous */}
          <Button variant="ghost" onClick={onCancel} disabled={isLoading}>
            ยกเลิก
          </Button>
          {/* Confirm: danger (red) for destructive, primary for normal confirmations */}
          <Button
            variant={isDanger ? 'danger' : 'primary'}
            onClick={onConfirm}
            isLoading={isLoading}
            data-testid="confirm-dialog-confirm-btn"
          >
            {confirmLabel}
          </Button>
        </>
      }
    >
      <p className="text-body-md text-on-surface leading-thai">{description}</p>
    </Modal>
  )
}

export default ConfirmDialog
