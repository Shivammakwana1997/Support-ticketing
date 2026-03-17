export function Footer() {
  return (
    <footer className="py-4 px-6 border-t border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
      <p className="text-xs text-neutral-500 text-center">
        &copy; {new Date().getFullYear()} SupportAI. All rights reserved.
      </p>
    </footer>
  );
}
