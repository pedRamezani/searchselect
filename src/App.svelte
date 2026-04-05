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
	import DataTableCheckbox from '$lib/data-table/data-table-checkbox.svelte';
	import DataTableTermButton from '$lib/data-table/data-table-term-button.svelte';

	// Components
	import { Button } from '$lib/components/ui/button/index.js';
	import CopyButton from '$lib/components/ui/copy-button/copy-button.svelte';
	import * as InputGroup from '$lib/components/ui/input-group/index.js';
	import {
		FlexRender,
		createSvelteTable,
		renderComponent
	} from '$lib/components/ui/data-table/index.js';
	import { ScrollArea } from '$lib/components/ui/scroll-area/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
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
	function termLengthFmt(length: number): string {
		if (length === 0) {
			return 'No terms';
		} else if (length === 1) {
			return '1 unique term';
		} else {
			return `${length} unique terms`;
		}
	}

	// Data loading
	let { bindings }: { bindings: { terms: string[]; selected: string[]; filtered: string[] } } =
		$props();
	let uniqueTerms = $derived<string[]>(Array.from(new Set(bindings.terms)));
	const termLengthDescription = $derived<string>(termLengthFmt(uniqueTerms.length));

	// Table setup
	type Terms = {
		id: string;
		term: string;
	};

	const data = $derived<Terms[]>(
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
					class: 'has-[>svg]:px-0 text-sm leading-none font-medium',
					onclick: column.getToggleSortingHandler()
				}),
			enableHiding: false,
			filterFn: termsFilterFn
		}
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
	const currentStateDescription = $derived<string>(
		searchTerm === '' ? termLengthDescription : searchTermValid ? '' : 'Invalid regex'
	);

	const onSearchTermChange = (searchTerm: string) => {
		table.getColumn('term')?.setFilterValue(searchTerm);
	};

	// Output formats
	const outputFormats = [
		{ value: 'python', label: 'Python list' },
		{ value: 'polars', label: 'Polars expression' }
	] as const;

	let outputFormat = $state<(typeof outputFormats)[number]['value']>('python');
	const outputFormatTriggerContent = $derived<string>(
		outputFormats.find((f) => f.value === outputFormat)?.label ?? 'Select an output format'
	);

	const quotedSelectedTerms = $derived<string[]>(
		table.getFilteredSelectedRowModel().rows.map((row) => `"${row.getValue('term')}"`)
	);
	const indentedJoinedQuotedSelectedTerms = $derived<string | null>(
		quotedSelectedTerms.length > 0
			? `<span class="ps-[2ch] block">${quotedSelectedTerms
					.map((quoted) => `<span class="inline-block font-semibold text-chart-2">${quoted}</span>`)
					.join(', ')}</span>`
			: null
	);

	const rawPythonList = $derived(`[${quotedSelectedTerms.join(', ')}]`);
	const pythonList = $derived(`[${indentedJoinedQuotedSelectedTerms ?? ''}]`);

	const rawPolarsExpr = $derived(`pl.col(${quotedSelectedTerms.join(', ')})`);
	const polarsExpr = $derived(`pl.col(${indentedJoinedQuotedSelectedTerms ?? '[]'})`);

	const rawOutput = $derived(outputFormat === 'python' ? rawPythonList : rawPolarsExpr);
	const output = $derived(outputFormat === 'python' ? pythonList : polarsExpr);

	// Selection
	// Select full text if clicked, but allows dragging for user to select substrings
	// Drag treshold
	const delta: number = 6 as const;
	let startX: number | undefined;
	let startY: number | undefined;

	function preMouseDown(
		event: MouseEvent & {
			currentTarget: EventTarget & HTMLDivElement;
		}
	) {
		startX = event.pageX;
		startY = event.pageY;
	}

	function preMouseUp(
		event: MouseEvent & {
			currentTarget: EventTarget & HTMLDivElement;
		}
	) {
		const smallDiffX = startX === undefined || Math.abs(event.pageX - startX) < delta;
		const smallDiffY = startY === undefined || Math.abs(event.pageY - startY) < delta;

		if (smallDiffX && smallDiffY) {
			const el = event.currentTarget.querySelector('pre');
			if (el && window.getSelection && document.createRange) {
				const sel = window.getSelection();
				const range = document.createRange();
				range.selectNodeContents(el);
				sel?.removeAllRanges();
				sel?.addRange(range);
			}
		}
	}

	// Binding synchronisation
	$effect(() => {
		bindings.selected = table.getFilteredSelectedRowModel().rows.map((row) => row.getValue('term'));
	});
	$effect(() => {
		bindings.filtered = table.getFilteredRowModel().rows.map((row) => row.getValue('term'));
	});
</script>

<div id="search-widget" class="my-4 flex w-full max-w-lg flex-col gap-4">
	<div class="flex flex-col gap-2 md:flex-row">
		<InputGroup.Root class="max-w-md">
			<InputGroup.Input
				bind:value={searchTerm}
				aria-invalid={!searchTermValid}
				placeholder="Filter terms..."
				oninput={(e) => onSearchTermChange(e.currentTarget.value)}
				onchange={(e) => onSearchTermChange(e.currentTarget.value)}
			/>
			<InputGroup.Addon>
				<SearchIcon />
			</InputGroup.Addon>
			<InputGroup.Addon align="inline-end">{currentStateDescription}</InputGroup.Addon>
		</InputGroup.Root>

		<ToggleGroup.Root
			bind:value={searchOptions}
			onValueChange={() => onSearchTermChange(searchTerm)}
			variant="outline"
			size="sm"
			type="multiple"
		>
			<ToggleGroup.Item value="case-insensitive" aria-label="Toggle case insensitive">
				<CaseSensitiveIcon class="size-4" />
			</ToggleGroup.Item>
			<ToggleGroup.Item value="regex" aria-label="Toggle regex">
				<RegexIcon class="size-4" />
			</ToggleGroup.Item>
		</ToggleGroup.Root>
	</div>
	<style>
		/* 
		VS-Code specific CSS fixes
		This is needed to override some weird table styles with higher specificity.
		*/

		table,
		thead,
		tr,
		th,
		td,
		tbody {
			border-color: var(--input);
			border-spacing: 0;
			border-collapse: collapse;
		}

		table {
			border-style: solid;
			border-color: var(--input);
			border-width: 1px;
		}

		table,
		th,
		tr {
			vertical-align: middle;
			text-align: left;
			border-bottom-style: solid;
			border-bottom-color: var(--input);
			border-bottom-width: 1px;
		}

		thead {
			font-weight: medium;
			background-color: unset;
		}

		thead tr[data-state='selected'] {
			background-color: var(--muted);
		}

		th th:has([role='checkbox']) {
			padding-right: calc(var(--spacing) * 0);
			padding-inline-start: calc(var(--spacing) * 3);
		}

		td {
			padding: calc(var(--spacing) * 2);
		}

		tr:nth-child(even) {
			background-color: unset;
		}

		tr:nth-child(even):hover {
			background-color: color-mix(in oklab, var(--muted) 50%, transparent);
		}

		tr:nth-child(even)[data-state='selected'] {
			background-color: var(--muted);
		}
	</style>
	<Table.Root class="rounded border border-input">
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
	<div class="flex items-center justify-end space-x-2">
		<div class="flex-1 text-sm text-muted-foreground">
			{table.getFilteredSelectedRowModel().rows.length} of
			{table.getFilteredRowModel().rows.length} term(s) selected.
		</div>
		<div class="space-x-2">
			<Button
				variant="outline"
				size="sm"
				class="border-input"
				onclick={() => table.previousPage()}
				disabled={!table.getCanPreviousPage()}
			>
				Previous
			</Button>
			<Button
				variant="outline"
				size="sm"
				class="border-input"
				onclick={() => table.nextPage()}
				disabled={!table.getCanNextPage()}
			>
				Next
			</Button>
		</div>
	</div>
	<ScrollArea class="h-48 rounded border border-input">
		<div
			class="relative p-4"
			onmousedown={preMouseDown}
			onmouseup={preMouseUp}
			role="textbox"
			tabindex="0"
		>
			<Select.Root type="single" name="favoriteFruit" bind:value={outputFormat}>
				<Select.Trigger class="mb-2 border-none p-0 text-sm leading-none font-medium">
					{outputFormatTriggerContent}
				</Select.Trigger>
				<Select.Content>
					{#each outputFormats as output (output.value)}
						<Select.Item value={output.value} label={output.label}>
							{output.label}
						</Select.Item>
					{/each}
				</Select.Content>
			</Select.Root>
			<pre class="text-wrap">{@html output}</pre>
			<CopyButton class="absolute top-2 right-2" text={rawOutput} />
		</div>
	</ScrollArea>
</div>
