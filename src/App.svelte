<script lang="ts">
	import { untrack } from 'svelte';

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
	import DataTableItemButton from '$lib/data-table/data-table-item-button.svelte';

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
	function itemLengthFmt(length: number): string {
		if (length === 0) {
			return 'No items';
		} else if (length === 1) {
			return '1 item';
		} else {
			return `${length} items`;
		}
	}

	/** Order-sensitive list equality, used to break sync loops between Python and the UI. */
	function sameList(a: string[], b: string[]): boolean {
		return a.length === b.length && a.every((value, index) => value === b[index]);
	}

	// Data loading
	let { bindings }: { bindings: { items: string[]; selected: string[]; filtered: string[] } } =
		$props();
	// Python normalises `items` on the way in (dedupes, first occurrence wins,
	// order otherwise preserved), so it is taken at face value here.
	const items = $derived<string[]>(bindings.items);
	const itemLengthDescription = $derived<string>(itemLengthFmt(items.length));

	// Table setup
	type Item = {
		item: string;
	};

	const data = $derived<Item[]>(items.map((item) => ({ item })));

	// NOTE: TanStack drops empty-string filters before ever calling this
	// (`shouldAutoRemoveFilter`), so an empty search box means "no filter" and
	// every item survives. There is deliberately no empty-string branch here.
	const itemsFilterFn: FilterFn<Item> = (row: Row<Item>, columnId: string) => {
		const item = row.getValue(columnId) as string;

		if (queryOptions.includes('regex')) {
			const flags = queryOptions.includes('case-insensitive') ? 'i' : '';
			return queryValid && new RegExp(query, flags).test(item);
		}

		if (queryOptions.includes('case-insensitive')) {
			return item.toLowerCase().includes(query.toLowerCase());
		}

		return item.includes(query);
	};

	const columns: ColumnDef<Item>[] = [
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
			accessorKey: 'item',
			header: ({ column }) =>
				renderComponent(DataTableItemButton, {
					class: 'has-[>svg]:px-0 text-sm leading-none font-medium',
					onclick: column.getToggleSortingHandler()
				}),
			enableHiding: false,
			filterFn: itemsFilterFn
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
		// Key selection on the item itself, not its position. Without this,
		// reassigning `items` from Python leaves ticks on whatever string has
		// moved into that row index.
		getRowId: (row) => row.item,
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
	let queryOptions = $state<string[]>([]);
	let query = $derived<string>(
		(table.getColumn('item')?.getFilterValue() as string | undefined) ?? ''
	);

	const queryValid = $derived.by<boolean>(() => {
		if (query === '') {
			return true;
		}

		if (queryOptions.includes('regex')) {
			try {
				const flags = queryOptions.includes('case-insensitive') ? 'i' : '';
				new RegExp(query, flags);
				return true;
			} catch (e) {
				return false;
			}
		}

		return true;
	});
	const currentStateDescription = $derived<string>(
		query === '' ? itemLengthDescription : queryValid ? '' : 'Invalid regex'
	);

	const onQueryChange = (query: string) => {
		table.getColumn('item')?.setFilterValue(query);
	};

	// Results
	//
	// `selected` is an explicit choice, so it deliberately survives the current
	// query — it is read off `rowSelection` against the full item list, not off
	// the filtered row model. Filtering the table does not unselect anything.
	// `filtered` is a query result: with an empty search box it is every item.
	const selectedItems = $derived<string[]>(items.filter((item) => rowSelection[item]));
	const filteredItems = $derived<string[]>(
		table.getFilteredRowModel().rows.map((row) => row.getValue('item') as string)
	);

	// Output formats
	const outputFormats = [
		{ value: 'python', label: 'Python list' },
		{ value: 'polars', label: 'Polars expression' }
	] as const;

	let outputFormat = $state<(typeof outputFormats)[number]['value']>('python');
	const outputFormatTriggerContent = $derived<string>(
		outputFormats.find((f) => f.value === outputFormat)?.label ?? 'Select an output format'
	);

	const quotedSelectedItems = $derived<string[]>(selectedItems.map((item) => `"${item}"`));
	const indentedJoinedQuotedSelectedItems = $derived<string | null>(
		quotedSelectedItems.length > 0
			? `<span class="ps-[2ch] block">${quotedSelectedItems
					.map((quoted) => `<span class="inline-block font-semibold text-chart-2">${quoted}</span>`)
					.join(', ')}</span>`
			: null
	);

	const rawPythonList = $derived(`[${quotedSelectedItems.join(', ')}]`);
	const pythonList = $derived(`[${indentedJoinedQuotedSelectedItems ?? ''}]`);

	const rawPolarsExpr = $derived(`pl.col(${quotedSelectedItems.join(', ')})`);
	const polarsExpr = $derived(`pl.col(${indentedJoinedQuotedSelectedItems ?? '[]'})`);

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
	//
	// Python -> UI. Unknown values are dropped, which is what makes reassigning
	// `items` keep ticks on items that still exist and discard the rest.
	$effect(() => {
		const incoming = bindings.selected;
		if (
			sameList(
				incoming,
				untrack(() => selectedItems)
			)
		)
			return;

		const known = new Set(untrack(() => items));
		rowSelection = Object.fromEntries(
			incoming.filter((item) => known.has(item)).map((item) => [item, true])
		);
	});

	// UI -> Python. Selection is click-driven and low frequency, so it syncs
	// immediately; `filtered` changes on every keystroke, so it is debounced.
	$effect(() => {
		const outgoing = selectedItems;
		if (
			!sameList(
				untrack(() => bindings.selected),
				outgoing
			)
		) {
			bindings.selected = outgoing;
		}
	});

	$effect(() => {
		const outgoing = filteredItems;
		const timer = setTimeout(() => {
			if (
				!sameList(
					untrack(() => bindings.filtered),
					outgoing
				)
			) {
				bindings.filtered = outgoing;
			}
		}, 150);
		return () => clearTimeout(timer);
	});
</script>

<div id="search-widget" class="my-4 flex w-full max-w-lg flex-col gap-4">
	<div class="flex flex-col gap-2 md:flex-row">
		<InputGroup.Root class="max-w-md">
			<InputGroup.Input
				bind:value={query}
				aria-invalid={!queryValid}
				placeholder="Filter items..."
				oninput={(e) => onQueryChange(e.currentTarget.value)}
				onchange={(e) => onQueryChange(e.currentTarget.value)}
			/>
			<InputGroup.Addon>
				<SearchIcon />
			</InputGroup.Addon>
			<InputGroup.Addon align="inline-end">{currentStateDescription}</InputGroup.Addon>
		</InputGroup.Root>

		<ToggleGroup.Root
			bind:value={queryOptions}
			onValueChange={() => onQueryChange(query)}
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
			{selectedItems.length} selected · {filteredItems.length} shown
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

<style>
	/*
	VS Code specific CSS fixes.

	VS Code's notebook stylesheet styles bare `table`/`tr`/`td` elements, so these
	rules exist to win that fight. They are confined to `#search-widget` and go
	through Svelte's scoper, which also appends this component's scope class — so
	they out-specify VS Code without leaking onto other tables in the notebook
	(pandas reprs, other widgets). Do NOT move this back inside the markup: a
	style element in a template is emitted as a literal, unscoped DOM node and
	restyles the entire page.
	*/

	#search-widget :global(table),
	#search-widget :global(thead),
	#search-widget :global(tr),
	#search-widget :global(th),
	#search-widget :global(td),
	#search-widget :global(tbody) {
		border-color: var(--input);
		border-spacing: 0;
		border-collapse: collapse;
	}

	#search-widget :global(table) {
		border-style: solid;
		border-color: var(--input);
		border-width: 1px;
	}

	#search-widget :global(table),
	#search-widget :global(th),
	#search-widget :global(tr) {
		vertical-align: middle;
		text-align: left;
		border-bottom-style: solid;
		border-bottom-color: var(--input);
		border-bottom-width: 1px;
	}

	#search-widget :global(thead) {
		font-weight: medium;
		background-color: unset;
	}

	#search-widget :global(thead tr[data-state='selected']) {
		background-color: var(--muted);
	}

	#search-widget :global(td) {
		padding: calc(var(--spacing) * 2);
	}

	#search-widget :global(tr:nth-child(even)) {
		background-color: unset;
	}

	#search-widget :global(tr:nth-child(even):hover) {
		background-color: color-mix(in oklab, var(--muted) 50%, transparent);
	}

	#search-widget :global(tr:nth-child(even)[data-state='selected']) {
		background-color: var(--muted);
	}
</style>
