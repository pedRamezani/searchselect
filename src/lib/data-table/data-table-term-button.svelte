<script lang="ts">
	import type { ComponentProps } from 'svelte';
	import ArrowUpDownIcon from '@lucide/svelte/icons/arrow-up-down';
	import { Button } from '$lib/components/ui/button/index.js';

	let { variant = 'ghost', size = 'sm', ...restProps }: ComponentProps<typeof Button> = $props();
</script>

<Button {variant} {size} {...restProps}>
	Term
	<ArrowUpDownIcon class="ms-2" />
</Button>
