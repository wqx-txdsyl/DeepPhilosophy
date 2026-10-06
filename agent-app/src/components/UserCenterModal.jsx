import SettingsPanel from './conversation/SettingsPanel';

/** Compatibility entry: account details now live in the single settings surface. */
export default function UserCenterModal({ onClose }) {
  return <SettingsPanel open initialSection="account" onClose={onClose} />;
}
