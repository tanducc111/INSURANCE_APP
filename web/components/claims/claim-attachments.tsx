import { ExternalLink, FileText, Image as ImageIcon, Trash2 } from "lucide-react";

import { toApiUrl } from "@/services/api-client";
import type { ClaimAttachment } from "@/types/claim";

function formatFileSize(size?: number | null) {
  if (!size) {
    return "Không rõ dung lượng";
  }
  if (size < 1024 * 1024) {
    return `${Math.max(1, Math.round(size / 1024))} KB`;
  }
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function isImage(attachment: ClaimAttachment) {
  return attachment.mime_type?.startsWith("image/");
}

type ClaimAttachmentsProps = {
  attachments: ClaimAttachment[];
  emptyText?: string;
  onDelete?: (attachment: ClaimAttachment) => void;
  isDeleting?: boolean;
};

export function ClaimAttachments({
  attachments,
  emptyText = "Chưa có tệp đính kèm nào.",
  onDelete,
  isDeleting = false,
}: ClaimAttachmentsProps) {
  if (attachments.length === 0) {
    return <p className="text-sm font-medium text-slate-500">{emptyText}</p>;
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {attachments.map((attachment) => {
        const fileUrl = toApiUrl(attachment.file_url);
        const image = isImage(attachment);

        return (
          <div
            className="overflow-hidden rounded-md border border-slate-200 bg-white"
            key={attachment.id}
          >
            {image ? (
              <a
                aria-label={`Xem ảnh ${attachment.file_name}`}
                href={fileUrl}
                rel="noreferrer"
                target="_blank"
              >
                <img
                  alt={attachment.file_name}
                  className="h-36 w-full bg-slate-100 object-cover"
                  src={fileUrl}
                />
              </a>
            ) : (
              <a
                className="flex h-36 items-center justify-center bg-slate-50 text-ocean"
                href={fileUrl}
                rel="noreferrer"
                target="_blank"
              >
                <FileText className="h-10 w-10" aria-hidden="true" />
                <span className="sr-only">Mở tài liệu</span>
              </a>
            )}

            <div className="space-y-3 p-3">
              <div>
                <p className="line-clamp-2 text-sm font-semibold text-slate-900">
                  {attachment.file_name}
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  {image ? "Ảnh chứng từ" : "Tài liệu PDF"} ·{" "}
                  {formatFileSize(attachment.file_size)}
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                <a
                  className="inline-flex items-center gap-1 rounded-md border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                  href={fileUrl}
                  rel="noreferrer"
                  target="_blank"
                >
                  {image ? (
                    <ImageIcon className="h-3.5 w-3.5" aria-hidden="true" />
                  ) : (
                    <FileText className="h-3.5 w-3.5" aria-hidden="true" />
                  )}
                  {image ? "Xem ảnh" : "Mở tài liệu"}
                  <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
                </a>
                {onDelete ? (
                  <button
                    className="inline-flex items-center gap-1 rounded-md border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50 disabled:opacity-60"
                    disabled={isDeleting}
                    onClick={() => onDelete(attachment)}
                    type="button"
                  >
                    <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                    Xóa tệp
                  </button>
                ) : null}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
