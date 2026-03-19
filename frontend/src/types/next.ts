export interface PageProps<
  TParams extends Record<string, string> = Record<string, string>,
  TSearchParams extends Record<string, string | string[] | undefined> = Record<
    string,
    string | string[] | undefined
  >,
> {
  params: Promise<TParams>;
  searchParams: Promise<TSearchParams>;
}

export interface LayoutProps<
  TParams extends Record<string, string> = Record<string, string>,
> {
  children: React.ReactNode;
  params: Promise<TParams>;
}
