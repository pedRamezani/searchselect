<script lang="ts">
	import { untrack } from 'svelte';

	// Data table imports
	import {
		type ColumnDef,
		type RowSelectionState,
		type SortingState,
		type VisibilityState,
		getCoreRowModel,
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
	//
	// Matching happens in Python, so the pattern the user types is a Python
	// regex they can paste into their own code. This component renders the
	// result rather than computing it: no filter function, no column filters,
	// no filtered row model. `filtered` is absent because Python derives it --
	// `_matches` stays empty while the query is, so the resting state costs no
	// list traffic instead of echoing every item back to say "everything".
	let {
		bindings
	}: {
		bindings: {
			items: string[];
			selected: string[];
			query: string;
			regex: boolean;
			case_sensitive: boolean;
			query_error: string;
			_matches: string[];
		};
	} = $props();
	// Python normalises `items` on the way in (dedupes, first occurrence wins,
	// order otherwise preserved), so it is taken at face value here.
	const items = $derived<string[]>(bindings.items);
	const itemLengthDescription = $derived<string>(itemLengthFmt(items.length));

	// Table setup
	type Item = {
		item: string;
	};

	// An empty query means everything, and Python does not resend the item list
	// to say so.
	const shownItems = $derived<string[]>(bindings.query === '' ? items : (bindings._matches ?? []));
	const data = $derived<Item[]>(shownItems.map((item) => ({ item })));

	const columns: ColumnDef<Item>[] = [
		{
			id: 'select',
			// Deliberately the all-rows variants, not the page variants: with the
			// list virtualised there are no pages, and "select all" should mean
			// "everything matching the current query" -- the click-free path to
			// the same set `filtered` reports.
			header: ({ table }) =>
				renderComponent(DataTableCheckbox, {
					checked: table.getIsAllRowsSelected(),
					indeterminate: table.getIsSomeRowsSelected() && !table.getIsAllRowsSelected(),
					onCheckedChange: (value) => table.toggleAllRowsSelected(!!value),
					'aria-label': 'Select all matching items'
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
			enableHiding: false
		}
	];

	let sorting = $state<SortingState>([]);
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
			get sorting() {
				return sorting;
			},
			get columnVisibility() {
				return columnVisibility;
			},
			get rowSelection() {
				return rowSelection;
			}
		},
		getCoreRowModel: getCoreRowModel(),
		getSortedRowModel: getSortedRowModel(),
		onSortingChange: (updater) => {
			if (typeof updater === 'function') {
				sorting = updater(sorting);
			} else {
				sorting = updater;
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
	//
	// The input is local so typing stays responsive, and is pushed to Python on
	// a debounce: every query costs a round trip now that Python does the
	// matching, so a keystroke must not become a request.
	let queryInput = $state('');

	// Python -> UI, for when the query is set programmatically.
	$effect(() => {
		const incoming = bindings.query;
		if (incoming !== untrack(() => queryInput)) {
			queryInput = incoming;
		}
	});

	$effect(() => {
		const outgoing = queryInput;
		const timer = setTimeout(() => {
			if (untrack(() => bindings.query) !== outgoing) {
				bindings.query = outgoing;
			}
		}, 150);
		return () => clearTimeout(timer);
	});

	// True while the kernel has not yet answered for what has been typed. Also
	// true, and stuck, if the kernel is busy -- which is the price of matching
	// in Python.
	const pending = $derived(queryInput !== bindings.query);

	// The toggles are Python traits, so a mode can be set from either side. The
	// UI models them as a multi-select of string values; Python models them as
	// two booleans, which is the better shape to read in a notebook.
	const queryModes = $derived<string[]>(
		[bindings.case_sensitive ? null : 'case-insensitive', bindings.regex ? 'regex' : null].filter(
			(mode): mode is string => mode !== null
		)
	);

	const onQueryModesChange = (modes: string[]) => {
		bindings.case_sensitive = !modes.includes('case-insensitive');
		bindings.regex = modes.includes('regex');
	};

	// Python reports the real `re.error`, which says far more than "invalid".
	const queryError = $derived<string>(bindings.query_error ?? '');
	const queryValid = $derived<boolean>(queryError === '');

	const currentStateDescription = $derived<string>(
		!queryValid ? queryError : queryInput === '' ? itemLengthDescription : pending ? '…' : ''
	);

	// Results
	//
	// `selected` is an explicit choice, so it deliberately survives the current
	// query — it is read off `rowSelection` against the full item list, not off
	// what is currently shown. Filtering the table does not unselect anything.
	const selectedItems = $derived<string[]>(items.filter((item) => rowSelection[item]));

	// Virtual window
	//
	// The visible slice is pure arithmetic over a measured row height -- no
	// dependency, no per-row observers. This bounds the DOM, not the row model:
	// the table still builds a Row per shown item, so a broad query over a very
	// large list is the remaining wall.
	const OVERSCAN = 8;

	const rows = $derived(table.getRowModel().rows);

	let scrollEl = $state<HTMLElement | undefined>();
	let scrollTop = $state(0);
	let viewportHeight = $state(0);

	// Seeded from the CSS below, then corrected from a real rendered row. The
	// host notebook restyles tables aggressively (see the VS Code fixes at the
	// bottom of this file), so measuring beats trusting a constant: if a row is
	// not the height we assumed, the spacers drift and the scrollbar lies.
	let rowHeight = $state(37);

	$effect(() => {
		// Depend on the rendered slice so this re-measures after a re-render.
		visibleRows;
		const probe = scrollEl?.querySelector<HTMLElement>('tbody tr:not([aria-hidden])');
		const measured = probe?.offsetHeight ?? 0;
		if (measured > 0 && measured !== untrack(() => rowHeight)) {
			rowHeight = measured;
		}
	});

	const firstVisible = $derived(Math.max(0, Math.floor(scrollTop / rowHeight) - OVERSCAN));
	const lastVisible = $derived(
		Math.min(rows.length, Math.ceil((scrollTop + viewportHeight) / rowHeight) + OVERSCAN)
	);
	const visibleRows = $derived(rows.slice(firstVisible, lastVisible));
	const padTop = $derived(firstVisible * rowHeight);
	const padBottom = $derived(Math.max(0, (rows.length - lastVisible) * rowHeight));

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

	// The query itself is synced above, next to the input it belongs to. There
	// is deliberately no effect sending matches: Python computes them.
</script>

<div id="search-widget" class="my-4 flex w-full max-w-lg flex-col gap-4">
	<div class="flex flex-col gap-2 md:flex-row">
		<InputGroup.Root class="max-w-md">
			<InputGroup.Input
				bind:value={queryInput}
				aria-invalid={!queryValid}
				placeholder="Filter items..."
				title={queryError}
			/>
			<InputGroup.Addon>
				<SearchIcon />
			</InputGroup.Addon>
			<InputGroup.Addon
				align="inline-end"
				class={cn('truncate', !queryValid && 'text-destructive')}
			>
				{currentStateDescription}
			</InputGroup.Addon>
		</InputGroup.Root>

		<ToggleGroup.Root
			value={queryModes}
			onValueChange={onQueryModesChange}
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
	<div
		bind:this={scrollEl}
		class="relative h-72 overflow-y-auto rounded border border-input"
		onscroll={(e) => (scrollTop = e.currentTarget.scrollTop)}
		bind:clientHeight={viewportHeight}
	>
		<Table.Root>
			<Table.Header>
				{#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
					<Table.Row>
						{#each headerGroup.headers as header (header.id)}
							<Table.Head
								class={cn(
									'sticky top-0 z-10 border-b border-input bg-background [&:has([role=checkbox])]:ps-3',
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
				{#if rows.length === 0}
					<Table.Row class="border-b border-input">
						<Table.Cell colspan={columns.length} class="h-24 text-center">No results.</Table.Cell>
					</Table.Row>
				{:else}
					<!-- Spacers stand in for the rows outside the window, so the
					     scrollbar reflects the whole list while the DOM holds only
					     what is on screen. -->
					{#if padTop > 0}
						<tr aria-hidden="true" style="height: {padTop}px"></tr>
					{/if}
					{#each visibleRows as row (row.id)}
						<Table.Row data-state={row.getIsSelected() && 'selected'} class="border-b border-input">
							{#each row.getVisibleCells() as cell (cell.id)}
								<Table.Cell class="[&:has([role=checkbox])]:ps-3">
									<FlexRender content={cell.column.columnDef.cell} context={cell.getContext()} />
								</Table.Cell>
							{/each}
						</Table.Row>
					{/each}
					{#if padBottom > 0}
						<tr aria-hidden="true" style="height: {padBottom}px"></tr>
					{/if}
				{/if}
			</Table.Body>
		</Table.Root>
	</div>
	<div class="flex items-center justify-between text-sm text-muted-foreground">
		<span>{selectedItems.length} selected · {shownItems.length} shown</span>
		{#if selectedItems.length > 0}
			<Button variant="outline" size="sm" class="border-input" onclick={() => (rowSelection = {})}>
				Clear selection
			</Button>
		{/if}
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

	/*
	The virtual window computes the visible slice from a constant row height, so
	rows must actually be that height -- otherwise the spacers drift and the
	scrollbar lies. Keep this in sync with ROW_HEIGHT in the script.
	*/
	#search-widget :global(tbody tr) {
		height: 37px;
	}

	#search-widget :global(tbody td) {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	/*
	Spacer rows stand in for off-screen rows. Their inline height wins over the
	rule above on specificity; they only need their borders suppressed so they
	do not draw as empty rows.
	*/
	#search-widget :global(tbody tr[aria-hidden='true']) {
		border: 0;
		padding: 0;
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
