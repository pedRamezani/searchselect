<script lang="ts">
	import * as InputGroup from '$lib/components/ui/input-group/index.js';
	import CaseSensitiveIcon from '@lucide/svelte/icons/case-sensitive';
	import RegexIcon from '@lucide/svelte/icons/regex';
	import * as ToggleGroup from '$lib/components/ui/toggle-group/index.js';
	import SearchIcon from '@lucide/svelte/icons/search';

	import { cn } from '$lib/utils';
	import './app.css';

	let { bindings }: { bindings: { terms: string[] } } = $props();
	let searchTerm = $state<string>('');
	let searchOptions = $state<string[]>([]);

	function termLengthFmt(length: number) {
		if (length === 0) {
			return 'No terms';
		} else if (length === 1) {
			return '1 term';
		} else {
			return `${length} terms`;
		}
	}

	const termLengthDescription = $derived(termLengthFmt(bindings.terms.length));

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

	const foundTerms = $derived.by<string[]>(() => {
		if (searchTerm === '') {
			return bindings.terms;
		} else {
			return bindings.terms.filter((term) => {
				if (searchOptions.includes('regex')) {
					const flags = searchOptions.includes('case-insensitive') ? 'i' : '';
					return searchTermValid && new RegExp(searchTerm, flags).test(term);
				}

				if (searchOptions.includes('case-insensitive')) {
					return term.toLowerCase().includes(searchTerm.toLowerCase());
				} else {
					return term.includes(searchTerm);
				}
			});
		}
	});

	const foundTermLengthDescription = $derived(termLengthFmt(foundTerms.length));

	const currentStateDescription = $derived.by<string>(() => {
		if (searchTerm === '') {
			return termLengthDescription;
		} else {
			return foundTermLengthDescription;
		}
	});
</script>

<div class="my-2 grid w-full max-w-sm gap-4">
	<InputGroup.Root>
		<InputGroup.Input
			bind:value={searchTerm}
			aria-invalid={!searchTermValid}
			placeholder="Search..."
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

	<ul class="list-disc pl-5">
		{#each foundTerms as term}
			<li>{term}</li>
		{/each}
	</ul>
</div>
