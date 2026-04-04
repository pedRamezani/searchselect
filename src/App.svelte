<script lang="ts">
	// Data table imports
	import {
		type ColumnDef,
		type ColumnFiltersState,
		type FilterFn,
		type PaginationState,
		type Row,
		type RowSelectionState,
		type SortingState,
		type VisibilityState,
		getCoreRowModel,
		getFilteredRowModel,
		getPaginationRowModel,
		getSortedRowModel
	} from '@tanstack/table-core';
	import { createRawSnippet } from 'svelte';
	import DataTableCheckbox from '$lib/data-table/data-table-checkbox.svelte';
	import DataTableTermButton from '$lib/data-table/data-table-term-button.svelte';

	// Components
	import { Button } from '$lib/components/ui/button/index.js';
	import * as InputGroup from '$lib/components/ui/input-group/index.js';
	import {
		FlexRender,
		createSvelteTable,
		renderComponent,
		renderSnippet
	} from '$lib/components/ui/data-table/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import * as ToggleGroup from '$lib/components/ui/toggle-group/index.js';

	// Icons
	import CaseSensitiveIcon from '@lucide/svelte/icons/case-sensitive';
	import RegexIcon from '@lucide/svelte/icons/regex';
	import SearchIcon from '@lucide/svelte/icons/search';

	// Styles
	import { cn } from '$lib/utils';
	import './app.css';

	// Helpers
	function termLengthFmt(length: number) {
		if (length === 0) {
			return 'No terms';
		} else if (length === 1) {
			return '1 unique term';
		} else {
			return `${length} unique terms`;
		}
	}

	// Data loading
	let { bindings }: { bindings: { terms: string[] } } = $props();
	let uniqueTerms = $derived(Array.from(new Set(bindings.terms)));
	const termLengthDescription = $derived(termLengthFmt(uniqueTerms.length));

	// Table setup
	type Terms = {
		id: string;
		term: string;
	};

	const data: Terms[] = $derived(
		uniqueTerms.map((term, index) => ({
			id: String(index),
			term
		}))
	);

	const termsFilterFn: FilterFn<Terms> = (
		row: Row<Terms>,
		columnId: string,
		filterValue: string
	) => {
		if (filterValue === '') {
			return false;
		} else {
			const term = row.getValue(columnId) as string;
			if (searchOptions.includes('regex')) {
				const flags = searchOptions.includes('case-insensitive') ? 'i' : '';
				return searchTermValid && new RegExp(searchTerm, flags).test(term);
			}

			if (searchOptions.includes('case-insensitive')) {
				return term.toLowerCase().includes(searchTerm.toLowerCase());
			} else {
				return term.includes(searchTerm);
			}
		}
	};

	const columns: ColumnDef<Terms>[] = [
		{
			id: 'select',
			header: ({ table }) =>
				renderComponent(DataTableCheckbox, {
					checked: table.getIsAllPageRowsSelected(),
					indeterminate: table.getIsSomePageRowsSelected() && !table.getIsAllPageRowsSelected(),
					onCheckedChange: (value) => table.toggleAllPageRowsSelected(!!value),
					'aria-label': 'Select all'
				}),
			cell: ({ row }) =>
				renderComponent(DataTableCheckbox, {
					checked: row.getIsSelected(),
					onCheckedChange: (value) => row.toggleSelected(!!value),
					'aria-label': 'Select row'
				}),
			enableResizing: false,
			enableSorting: false,
			enableHiding: false
		},
		{
			accessorKey: 'term',
			header: ({ column }) =>
				renderComponent(DataTableTermButton, {
					onclick: column.getToggleSortingHandler()
				}),
			cell: ({ row }) => {
				const termSnippet = createRawSnippet<[{ term: string }]>((getTerm) => {
					const { term } = getTerm();
					return {
						render: () => `<div class="lowercase">${term}</div>`
					};
				});

				return renderSnippet(termSnippet, {
					term: row.original.term
				});
			},
			enableHiding: false,
			filterFn: termsFilterFn
		}
		// {
		// 	id: 'actions',
		// 	enableHiding: false,
		// 	cell: ({ row }) => renderComponent(DataTableActions, { id: row.original.id })
		// }
	];

	let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 10 });
	let sorting = $state<SortingState>([]);
	let columnFilters = $state<ColumnFiltersState>([]);
	let rowSelection = $state<RowSelectionState>({});
	let columnVisibility = $state<VisibilityState>({});

	const table = createSvelteTable({
		get data() {
			return data;
		},
		columns,
		state: {
			get pagination() {
				return pagination;
			},
			get sorting() {
				return sorting;
			},
			get columnVisibility() {
				return columnVisibility;
			},
			get rowSelection() {
				return rowSelection;
			},
			get columnFilters() {
				return columnFilters;
			}
		},
		getCoreRowModel: getCoreRowModel(),
		getPaginationRowModel: getPaginationRowModel(),
		getSortedRowModel: getSortedRowModel(),
		getFilteredRowModel: getFilteredRowModel(),
		onPaginationChange: (updater) => {
			if (typeof updater === 'function') {
				pagination = updater(pagination);
			} else {
				pagination = updater;
			}
		},
		onSortingChange: (updater) => {
			if (typeof updater === 'function') {
				sorting = updater(sorting);
			} else {
				sorting = updater;
			}
		},
		onColumnFiltersChange: (updater) => {
			if (typeof updater === 'function') {
				columnFilters = updater(columnFilters);
			} else {
				columnFilters = updater;
			}
		},
		onColumnVisibilityChange: (updater) => {
			if (typeof updater === 'function') {
				columnVisibility = updater(columnVisibility);
			} else {
				columnVisibility = updater;
			}
		},
		onRowSelectionChange: (updater) => {
			if (typeof updater === 'function') {
				rowSelection = updater(rowSelection);
			} else {
				rowSelection = updater;
			}
		}
	});

	// Search setup
	let searchOptions = $state<string[]>([]);
	let searchTerm = $derived<string>(
		(table.getColumn('term')?.getFilterValue() as string | undefined) ?? ''
	);

	const searchTermValid = $derived.by<boolean>(() => {
		if (searchTerm === '') {
			return true;
		}

		if (searchOptions.includes('regex')) {
			try {
				const flags = searchOptions.includes('case-insensitive') ? 'i' : '';
				new RegExp(searchTerm, flags);
				return true;
			} catch (e) {
				return false;
			}
		}

		return true;
	});
	const currentStateDescription = $derived(
		searchTerm === '' ? termLengthDescription : searchTermValid ? '' : 'Invalid regex'
	);

	const onSearchTermChange = (
		e: Event & {
			currentTarget: EventTarget & HTMLInputElement;
		}
	) => {
		const target = e.currentTarget;
		table.getColumn('term')?.setFilterValue(target.value);
	};
</script>

<div class="my-4 flex w-full flex-col gap-4">
	<div class="flex flex-col gap-2 md:flex-row">
		<InputGroup.Root class="max-w-md">
			<InputGroup.Input
				bind:value={searchTerm}
				aria-invalid={!searchTermValid}
				placeholder="Filter terms..."
				oninput={onSearchTermChange}
				onchange={onSearchTermChange}
			/>
			<InputGroup.Addon>
				<SearchIcon />
			</InputGroup.Addon>
			<InputGroup.Addon align="inline-end">{currentStateDescription}</InputGroup.Addon>
		</InputGroup.Root>

		<ToggleGroup.Root bind:value={searchOptions} variant="outline" size="sm" type="multiple">
			<ToggleGroup.Item value="case-insensitive" aria-label="Toggle case insensitive">
				<CaseSensitiveIcon class="size-4" />
			</ToggleGroup.Item>
			<ToggleGroup.Item value="regex" aria-label="Toggle regex">
				<RegexIcon class="size-4" />
			</ToggleGroup.Item>
		</ToggleGroup.Root>
	</div>
	<Table.Root class="max-w-md rounded border border-input">
		<Table.Header>
			{#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
				<Table.Row>
					{#each headerGroup.headers as header (header.id)}
						<Table.Head
							class={cn(
								'border-b border-input [&:has([role=checkbox])]:ps-3',
								header.id === 'select' ? 'w-10' : undefined
							)}
						>
							{#if !header.isPlaceholder}
								<FlexRender
									content={header.column.columnDef.header}
									context={header.getContext()}
								/>
							{/if}
						</Table.Head>
					{/each}
				</Table.Row>
			{/each}
		</Table.Header>
		<Table.Body>
			{#each table.getRowModel().rows as row (row.id)}
				<Table.Row data-state={row.getIsSelected() && 'selected'} class="border-b border-input">
					{#each row.getVisibleCells() as cell (cell.id)}
						<Table.Cell class="[&:has([role=checkbox])]:ps-3">
							<FlexRender content={cell.column.columnDef.cell} context={cell.getContext()} />
						</Table.Cell>
					{/each}
				</Table.Row>
			{:else}
				<Table.Row class="border-b border-input">
					<Table.Cell colspan={columns.length} class="h-24 text-center">No results.</Table.Cell>
				</Table.Row>
			{/each}
		</Table.Body>
	</Table.Root>
	<div class="flex items-center justify-end space-x-2 pt-4">
		<div class="flex-1 text-sm text-muted-foreground">
			{table.getFilteredSelectedRowModel().rows.length} of
			{table.getFilteredRowModel().rows.length} term(s) selected.
		</div>
		<div class="space-x-2">
			<Button
				variant="outline"
				size="sm"
				onclick={() => table.previousPage()}
				disabled={!table.getCanPreviousPage()}
			>
				Previous
			</Button>
			<Button
				variant="outline"
				size="sm"
				onclick={() => table.nextPage()}
				disabled={!table.getCanNextPage()}
			>
				Next
			</Button>
		</div>
	</div>
</div>
